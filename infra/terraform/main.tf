# Terraform Configuration — AWS Infrastructure
# Smart Store Operations — Phase 8

terraform {
  required_version = ">= 1.7.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.40"
    }
  }

  backend "s3" {
    bucket         = "smartstore-terraform-state"
    key            = "production/terraform.tfstate"
    region         = "ap-south-1"
    encrypt        = true
    dynamodb_table = "terraform-locks"
  }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = "SmartStoreOperations"
      Environment = var.environment
      ManagedBy   = "Terraform"
    }
  }
}

# ─── Variables ────────────────────────────────────────────────────

variable "aws_region" {
  default = "ap-south-1"
}

variable "environment" {
  default = "production"
}

variable "cluster_name" {
  default = "smartstore-eks"
}

variable "db_password" {
  type      = string
  sensitive = true
}

# ─── VPC ──────────────────────────────────────────────────────────

module "vpc" {
  source  = "terraform-aws-modules/vpc/aws"
  version = "~> 5.5"

  name = "smartstore-vpc"
  cidr = "10.0.0.0/16"

  azs             = ["${var.aws_region}a", "${var.aws_region}b", "${var.aws_region}c"]
  private_subnets = ["10.0.1.0/24", "10.0.2.0/24", "10.0.3.0/24"]
  public_subnets  = ["10.0.101.0/24", "10.0.102.0/24", "10.0.103.0/24"]

  enable_nat_gateway   = true
  single_nat_gateway   = true
  enable_dns_hostnames = true

  public_subnet_tags = {
    "kubernetes.io/role/elb" = 1
  }

  private_subnet_tags = {
    "kubernetes.io/role/internal-elb" = 1
  }
}

# ─── EKS Cluster ──────────────────────────────────────────────────

module "eks" {
  source  = "terraform-aws-modules/eks/aws"
  version = "~> 20.0"

  cluster_name    = var.cluster_name
  cluster_version = "1.29"

  vpc_id     = module.vpc.vpc_id
  subnet_ids = module.vpc.private_subnets

  cluster_endpoint_public_access = true

  eks_managed_node_groups = {
    general = {
      desired_size = 3
      min_size     = 2
      max_size     = 6

      instance_types = ["m6i.large"]
      capacity_type  = "ON_DEMAND"

      labels = {
        workload = "general"
      }
    }

    ml_training = {
      desired_size = 0
      min_size     = 0
      max_size     = 4

      instance_types = ["g5.xlarge"]
      capacity_type  = "SPOT"

      labels = {
        workload = "ml-training"
      }

      taints = [{
        key    = "nvidia.com/gpu"
        value  = "true"
        effect = "NO_SCHEDULE"
      }]
    }
  }
}

# ─── S3 Data Lake ─────────────────────────────────────────────────

resource "aws_s3_bucket" "datalake" {
  bucket = "smartstore-datalake-${var.environment}"
}

resource "aws_s3_bucket_versioning" "datalake" {
  bucket = aws_s3_bucket.datalake.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_lifecycle_configuration" "datalake" {
  bucket = aws_s3_bucket.datalake.id

  rule {
    id     = "archive-old-data"
    status = "Enabled"

    transition {
      days          = 90
      storage_class = "GLACIER"
    }

    expiration {
      days = 730
    }
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "datalake" {
  bucket = aws_s3_bucket.datalake.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "aws:kms"
    }
  }
}

# ─── S3 for ML Models ────────────────────────────────────────────

resource "aws_s3_bucket" "models" {
  bucket = "smartstore-models-${var.environment}"
}

resource "aws_s3_bucket_versioning" "models" {
  bucket = aws_s3_bucket.models.id
  versioning_configuration {
    status = "Enabled"
  }
}

# ─── Kinesis Data Stream ─────────────────────────────────────────

resource "aws_kinesis_stream" "sensor_events" {
  name             = "smartstore-sensor-events"
  shard_count      = 4
  retention_period = 168 # 7 days

  stream_mode_details {
    stream_mode = "PROVISIONED"
  }

  encryption_type = "KMS"
}

resource "aws_kinesis_stream" "alerts" {
  name             = "smartstore-alerts"
  shard_count      = 2
  retention_period = 72

  stream_mode_details {
    stream_mode = "PROVISIONED"
  }

  encryption_type = "KMS"
}

# ─── RDS (TimescaleDB) ───────────────────────────────────────────

resource "aws_db_subnet_group" "main" {
  name       = "smartstore-db-subnet"
  subnet_ids = module.vpc.private_subnets
}

resource "aws_security_group" "rds" {
  name_prefix = "smartstore-rds-"
  vpc_id      = module.vpc.vpc_id

  ingress {
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [module.eks.cluster_security_group_id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_db_instance" "timescaledb" {
  identifier = "smartstore-timescaledb"

  engine         = "postgres"
  engine_version = "16.2"
  instance_class = "db.r6g.large"

  allocated_storage     = 100
  max_allocated_storage = 500
  storage_type          = "gp3"
  storage_encrypted     = true

  db_name  = "smartstore"
  username = "smartstore_admin"
  password = var.db_password

  db_subnet_group_name   = aws_db_subnet_group.main.name
  vpc_security_group_ids = [aws_security_group.rds.id]

  backup_retention_period = 14
  multi_az               = true
  deletion_protection    = true

  performance_insights_enabled = true
}

# ─── ElastiCache (Redis) ─────────────────────────────────────────

resource "aws_elasticache_subnet_group" "main" {
  name       = "smartstore-redis-subnet"
  subnet_ids = module.vpc.private_subnets
}

resource "aws_elasticache_replication_group" "redis" {
  replication_group_id = "smartstore-redis"
  description          = "Smart Store Redis for WebSocket pub/sub and caching"

  node_type            = "cache.r6g.large"
  num_cache_clusters   = 2
  engine               = "redis"
  engine_version       = "7.1"
  port                 = 6379

  subnet_group_name = aws_elasticache_subnet_group.main.name

  at_rest_encryption_enabled = true
  transit_encryption_enabled = true

  automatic_failover_enabled = true
}

# ─── Glue Data Catalog ───────────────────────────────────────────

resource "aws_glue_catalog_database" "datalake" {
  name = "smartstore_datalake"
}

resource "aws_glue_catalog_table" "shelf_state" {
  name          = "shelf_state"
  database_name = aws_glue_catalog_database.datalake.name

  table_type = "EXTERNAL_TABLE"

  parameters = {
    "classification" = "parquet"
  }

  storage_descriptor {
    location      = "s3://${aws_s3_bucket.datalake.bucket}/shelf_state/"
    input_format  = "org.apache.hadoop.hive.ql.io.parquet.MapredParquetInputFormat"
    output_format = "org.apache.hadoop.hive.ql.io.parquet.MapredParquetOutputFormat"

    ser_de_info {
      serialization_library = "org.apache.hadoop.hive.ql.io.parquet.serde.ParquetHiveSerDe"
    }

    columns {
      name = "store_id"
      type = "string"
    }
    columns {
      name = "aisle"
      type = "string"
    }
    columns {
      name = "bay"
      type = "int"
    }
    columns {
      name = "product_id"
      type = "string"
    }
    columns {
      name = "fused_confidence"
      type = "float"
    }
    columns {
      name = "is_out_of_stock"
      type = "boolean"
    }
    columns {
      name = "timestamp"
      type = "timestamp"
    }
  }

  partition_keys {
    name = "year"
    type = "string"
  }
  partition_keys {
    name = "month"
    type = "string"
  }
  partition_keys {
    name = "day"
    type = "string"
  }
}

# ─── Outputs ──────────────────────────────────────────────────────

output "eks_cluster_name" {
  value = module.eks.cluster_name
}

output "eks_cluster_endpoint" {
  value = module.eks.cluster_endpoint
}

output "datalake_bucket" {
  value = aws_s3_bucket.datalake.bucket
}

output "models_bucket" {
  value = aws_s3_bucket.models.bucket
}

output "rds_endpoint" {
  value = aws_db_instance.timescaledb.endpoint
}

output "redis_endpoint" {
  value = aws_elasticache_replication_group.redis.primary_endpoint_address
}
