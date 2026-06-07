"""
Smart Store Operations — YOLOv9 Shelf Detection Model Training
Phase 4: Computer Vision Pipeline

Fine-tunes YOLOv9-m on annotated shelf images for empty facing detection.
Target: mAP@0.5 >= 0.92, model size <= 120MB
"""

import os
import yaml
import logging
import argparse
from pathlib import Path
from datetime import datetime

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# ─── Configuration ────────────────────────────────────────────────────────────

DEFAULT_CONFIG = {
    "model": {
        "architecture": "yolov9-m",
        "pretrained_weights": "yolov9-m.pt",
        "input_size": 640,
        "num_classes": 4,
        "class_names": [
            "product_present",
            "empty_facing",
            "wrong_product",
            "partial_facing",
        ],
    },
    "training": {
        "epochs": 150,
        "batch_size": 16,
        "learning_rate": 0.001,
        "optimizer": "AdamW",
        "weight_decay": 0.0005,
        "warmup_epochs": 5,
        "lr_scheduler": "cosine",
        "early_stopping_patience": 20,
        "train_split": 0.70,
        "val_split": 0.15,
        "test_split": 0.15,
        "seed": 42,
    },
    "augmentation": {
        "rotation_range_deg": 15,
        "brightness_range_pct": 30,
        "horizontal_flip": True,
        "vertical_flip": False,
        "mosaic": True,
        "mosaic_prob": 0.5,
        "mixup": True,
        "mixup_prob": 0.3,
        "hsv_h": 0.015,
        "hsv_s": 0.7,
        "hsv_v": 0.4,
        "scale": 0.5,
        "translate": 0.1,
        "blur_limit": 3,
        "noise_std": 0.02,
    },
    "data": {
        "dataset_root": "./data/shelf_dataset",
        "images_per_category": 10000,
        "annotation_format": "yolo",
        "label_studio_project_id": "shelf_detection_v1",
    },
    "export": {
        "format": "tensorrt",
        "precision": "int8",
        "max_model_size_mb": 120,
        "target_device": "jetson_orin_nx",
        "max_inference_ms": 80,
    },
    "tracking": {
        "mlflow_experiment": "shelf_detection_yolov9",
        "dvc_remote": "s3://smartstore-models/shelf-detection",
    },
}


def create_dataset_yaml(config: dict, output_path: str) -> str:
    """Generate YOLO-format dataset.yaml for training."""
    dataset_config = {
        "path": os.path.abspath(config["data"]["dataset_root"]),
        "train": "images/train",
        "val": "images/val",
        "test": "images/test",
        "nc": config["model"]["num_classes"],
        "names": config["model"]["class_names"],
    }

    yaml_path = os.path.join(output_path, "dataset.yaml")
    with open(yaml_path, "w") as f:
        yaml.dump(dataset_config, f, default_flow_style=False)

    logger.info(f"Dataset YAML created at {yaml_path}")
    return yaml_path


def setup_augmentation_pipeline(config: dict):
    """Configure data augmentation using Albumentations."""
    try:
        import albumentations as A
    except ImportError:
        logger.warning("albumentations not installed, using default YOLO augmentations")
        return None

    aug_cfg = config["augmentation"]

    transform = A.Compose(
        [
            A.HorizontalFlip(p=0.5 if aug_cfg["horizontal_flip"] else 0.0),
            A.Rotate(
                limit=aug_cfg["rotation_range_deg"],
                p=0.4,
                border_mode=0,
            ),
            A.RandomBrightnessContrast(
                brightness_limit=aug_cfg["brightness_range_pct"] / 100.0,
                contrast_limit=0.2,
                p=0.5,
            ),
            A.HueSaturationValue(
                hue_shift_limit=int(aug_cfg["hsv_h"] * 255),
                sat_shift_limit=int(aug_cfg["hsv_s"] * 255),
                val_shift_limit=int(aug_cfg["hsv_v"] * 255),
                p=0.4,
            ),
            A.GaussianBlur(blur_limit=aug_cfg["blur_limit"], p=0.2),
            A.GaussNoise(p=0.2),
            A.RandomScale(scale_limit=aug_cfg["scale"], p=0.3),
        ],
        bbox_params=A.BboxParams(
            format="yolo",
            label_fields=["class_labels"],
            min_visibility=0.3,
        ),
    )
    logger.info("Augmentation pipeline configured with Albumentations")
    return transform


def split_dataset(config: dict):
    """Split dataset into train/val/test sets."""
    import random
    import shutil

    random.seed(config["training"]["seed"])

    dataset_root = Path(config["data"]["dataset_root"])
    all_images_dir = dataset_root / "images" / "all"
    all_labels_dir = dataset_root / "labels" / "all"

    if not all_images_dir.exists():
        logger.warning(f"Source directory {all_images_dir} not found. Creating directory structure...")
        for split in ["train", "val", "test"]:
            (dataset_root / "images" / split).mkdir(parents=True, exist_ok=True)
            (dataset_root / "labels" / split).mkdir(parents=True, exist_ok=True)
        logger.info("Directory structure created. Place images in 'images/all' and labels in 'labels/all'.")
        return

    image_files = sorted(list(all_images_dir.glob("*.jpg")) + list(all_images_dir.glob("*.png")))
    random.shuffle(image_files)

    n = len(image_files)
    train_end = int(n * config["training"]["train_split"])
    val_end = train_end + int(n * config["training"]["val_split"])

    splits = {
        "train": image_files[:train_end],
        "val": image_files[train_end:val_end],
        "test": image_files[val_end:],
    }

    for split_name, files in splits.items():
        img_dir = dataset_root / "images" / split_name
        lbl_dir = dataset_root / "labels" / split_name
        img_dir.mkdir(parents=True, exist_ok=True)
        lbl_dir.mkdir(parents=True, exist_ok=True)

        for img_path in files:
            shutil.copy2(img_path, img_dir / img_path.name)
            label_path = all_labels_dir / f"{img_path.stem}.txt"
            if label_path.exists():
                shutil.copy2(label_path, lbl_dir / label_path.name)

        logger.info(f"{split_name}: {len(files)} images")


def train_model(config: dict, dataset_yaml: str, output_dir: str):
    """Fine-tune YOLOv9-m on shelf detection dataset."""
    try:
        from ultralytics import YOLO
    except ImportError:
        logger.error("ultralytics package not installed. Install with: pip install ultralytics")
        logger.info("Generating training configuration for manual execution...")
        _save_training_config(config, dataset_yaml, output_dir)
        return None

    model_cfg = config["model"]
    train_cfg = config["training"]

    model = YOLO(model_cfg["pretrained_weights"])

    logger.info("=" * 60)
    logger.info("Starting YOLOv9-m Fine-Tuning")
    logger.info(f"  Architecture: {model_cfg['architecture']}")
    logger.info(f"  Input size: {model_cfg['input_size']}px")
    logger.info(f"  Classes: {model_cfg['num_classes']} — {model_cfg['class_names']}")
    logger.info(f"  Epochs: {train_cfg['epochs']}")
    logger.info(f"  Batch size: {train_cfg['batch_size']}")
    logger.info(f"  Learning rate: {train_cfg['learning_rate']}")
    logger.info("=" * 60)

    results = model.train(
        data=dataset_yaml,
        epochs=train_cfg["epochs"],
        batch=train_cfg["batch_size"],
        imgsz=model_cfg["input_size"],
        lr0=train_cfg["learning_rate"],
        optimizer=train_cfg["optimizer"],
        weight_decay=train_cfg["weight_decay"],
        warmup_epochs=train_cfg["warmup_epochs"],
        cos_lr=(train_cfg["lr_scheduler"] == "cosine"),
        patience=train_cfg["early_stopping_patience"],
        seed=train_cfg["seed"],
        project=output_dir,
        name="shelf_detection",
        augment=True,
        hsv_h=config["augmentation"]["hsv_h"],
        hsv_s=config["augmentation"]["hsv_s"],
        hsv_v=config["augmentation"]["hsv_v"],
        degrees=config["augmentation"]["rotation_range_deg"],
        translate=config["augmentation"]["translate"],
        scale=config["augmentation"]["scale"],
        flipud=0.0,
        fliplr=0.5 if config["augmentation"]["horizontal_flip"] else 0.0,
        mosaic=config["augmentation"]["mosaic_prob"],
        mixup=config["augmentation"]["mixup_prob"],
        device=0,
        workers=8,
        val=True,
        plots=True,
        save=True,
    )

    logger.info("Training complete.")
    return model, results


def evaluate_model(model, dataset_yaml: str, config: dict):
    """Evaluate model on test set and check against target metrics."""
    results = model.val(data=dataset_yaml, split="test")

    metrics = {
        "mAP50": results.box.map50,
        "mAP50-95": results.box.map,
        "precision": results.box.mp,
        "recall": results.box.mr,
    }

    logger.info("=" * 60)
    logger.info("Test Set Evaluation Results:")
    for k, v in metrics.items():
        status = "✓" if k == "mAP50" and v >= 0.92 else "○"
        logger.info(f"  {status} {k}: {v:.4f}")

    target_map = 0.92
    if metrics["mAP50"] >= target_map:
        logger.info(f"✓ Target mAP@0.5 >= {target_map} ACHIEVED ({metrics['mAP50']:.4f})")
    else:
        logger.warning(f"✗ Target mAP@0.5 >= {target_map} NOT MET ({metrics['mAP50']:.4f})")
        logger.warning("  Consider: more training data, longer training, hyperparameter tuning")

    return metrics


def export_tensorrt(model, config: dict, output_dir: str):
    """Export model to TensorRT INT8 for Jetson Orin NX deployment."""
    export_cfg = config["export"]

    logger.info("Exporting to TensorRT INT8...")
    exported_path = model.export(
        format="engine",
        half=False,
        int8=True,
        imgsz=config["model"]["input_size"],
        device=0,
        workspace=4,
    )

    model_size_mb = os.path.getsize(exported_path) / (1024 * 1024)
    logger.info(f"Exported model size: {model_size_mb:.1f} MB")

    if model_size_mb <= export_cfg["max_model_size_mb"]:
        logger.info(f"✓ Model size within limit ({export_cfg['max_model_size_mb']} MB)")
    else:
        logger.warning(f"✗ Model exceeds size limit: {model_size_mb:.1f} > {export_cfg['max_model_size_mb']} MB")

    return exported_path


def log_to_mlflow(config: dict, metrics: dict, model_path: str):
    """Log experiment to MLflow for tracking and model registry."""
    try:
        import mlflow
    except ImportError:
        logger.warning("MLflow not installed, skipping experiment tracking")
        return

    mlflow.set_experiment(config["tracking"]["mlflow_experiment"])

    with mlflow.start_run(run_name=f"yolov9m_{datetime.now().strftime('%Y%m%d_%H%M')}"):
        mlflow.log_params({
            "architecture": config["model"]["architecture"],
            "input_size": config["model"]["input_size"],
            "epochs": config["training"]["epochs"],
            "batch_size": config["training"]["batch_size"],
            "lr": config["training"]["learning_rate"],
            "optimizer": config["training"]["optimizer"],
        })

        mlflow.log_metrics(metrics)

        if os.path.exists(model_path):
            mlflow.log_artifact(model_path, artifact_path="models")

        logger.info("Experiment logged to MLflow")


def _save_training_config(config: dict, dataset_yaml: str, output_dir: str):
    """Save training configuration for offline/manual execution."""
    os.makedirs(output_dir, exist_ok=True)
    config_path = os.path.join(output_dir, "training_config.yaml")
    with open(config_path, "w") as f:
        yaml.dump(config, f, default_flow_style=False)
    logger.info(f"Training config saved to {config_path}")
    logger.info("Run manually with: yolo detect train data=dataset.yaml model=yolov9-m.pt epochs=150")


def main():
    parser = argparse.ArgumentParser(description="YOLOv9 Shelf Detection Training")
    parser.add_argument("--config", type=str, help="Path to custom config YAML")
    parser.add_argument("--output-dir", type=str, default="./runs/shelf_detection")
    parser.add_argument("--split-only", action="store_true", help="Only split dataset")
    parser.add_argument("--export-only", action="store_true", help="Only export model")
    parser.add_argument("--weights", type=str, help="Path to trained weights for export")
    args = parser.parse_args()

    config = DEFAULT_CONFIG.copy()
    if args.config:
        with open(args.config) as f:
            custom = yaml.safe_load(f)
            config.update(custom)

    os.makedirs(args.output_dir, exist_ok=True)

    # Step 1: Split dataset
    logger.info("Step 1: Splitting dataset...")
    split_dataset(config)

    if args.split_only:
        logger.info("Dataset split complete. Exiting.")
        return

    # Step 2: Create dataset YAML
    dataset_yaml = create_dataset_yaml(config, args.output_dir)

    # Step 3: Setup augmentation
    setup_augmentation_pipeline(config)

    if args.export_only and args.weights:
        from ultralytics import YOLO
        model = YOLO(args.weights)
        export_tensorrt(model, config, args.output_dir)
        return

    # Step 4: Train
    logger.info("Step 2: Training YOLOv9-m model...")
    result = train_model(config, dataset_yaml, args.output_dir)

    if result is None:
        logger.info("Training config saved. Run manually or install ultralytics.")
        return

    model, train_results = result

    # Step 5: Evaluate
    logger.info("Step 3: Evaluating on test set...")
    metrics = evaluate_model(model, dataset_yaml, config)

    # Step 6: Export
    logger.info("Step 4: Exporting to TensorRT INT8...")
    try:
        exported_path = export_tensorrt(model, config, args.output_dir)
    except Exception as e:
        logger.warning(f"TensorRT export failed (not on Jetson?): {e}")
        exported_path = str(Path(args.output_dir) / "best.pt")
        model.save(exported_path)

    # Step 7: Log
    logger.info("Step 5: Logging to MLflow...")
    log_to_mlflow(config, metrics, exported_path)

    logger.info("=" * 60)
    logger.info("YOLOv9 Shelf Detection Pipeline Complete!")
    logger.info(f"  Model: {exported_path}")
    logger.info(f"  mAP@0.5: {metrics.get('mAP50', 'N/A')}")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
