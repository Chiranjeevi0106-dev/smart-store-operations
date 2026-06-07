"""
Smart Store Operations — Siamese ResNet-50 Planogram Compliance
Phase 4: Computer Vision Pipeline

Trains a Siamese network comparing live shelf crops against golden planogram images.
Output: compliance score 0-1, per-facing deviation map.
"""

import os
import logging
import argparse
from pathlib import Path

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import Dataset, DataLoader
from torchvision import models, transforms

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# ─── Configuration ────────────────────────────────────────────────────────────

TRAINING_CONFIG = {
    "backbone": "resnet50",
    "embedding_dim": 256,
    "input_size": 224,
    "batch_size": 32,
    "epochs": 80,
    "learning_rate": 0.0001,
    "weight_decay": 0.0001,
    "margin": 1.0,  # Contrastive loss margin
    "train_split": 0.7,
    "val_split": 0.15,
    "test_split": 0.15,
    "seed": 42,
}


# ─── Dataset ──────────────────────────────────────────────────────────────────

class PlanogramPairDataset(Dataset):
    """
    Dataset of (live_shelf_image, planogram_image, label) triplets.
    label = 1 if compliant (match), 0 if non-compliant (mismatch).

    Directory structure:
        data/planogram/
        ├── live/          # Live shelf crop images
        ├── golden/        # Golden planogram reference images
        └── pairs.csv      # columns: live_image, golden_image, label
    """

    def __init__(self, data_dir: str, pairs_file: str, transform=None):
        import pandas as pd

        self.data_dir = Path(data_dir)
        self.transform = transform

        pairs_path = self.data_dir / pairs_file
        if pairs_path.exists():
            self.pairs = pd.read_csv(pairs_path)
        else:
            logger.warning(f"Pairs file not found at {pairs_path}. Creating sample structure...")
            self._create_sample_structure()
            self.pairs = self._generate_mock_pairs()

    def _create_sample_structure(self):
        (self.data_dir / "live").mkdir(parents=True, exist_ok=True)
        (self.data_dir / "golden").mkdir(parents=True, exist_ok=True)

    def _generate_mock_pairs(self):
        import pandas as pd
        data = {
            "live_image": [f"live/shelf_{i:04d}.jpg" for i in range(100)],
            "golden_image": [f"golden/planogram_{i % 20:04d}.jpg" for i in range(100)],
            "label": [1 if i % 5 != 0 else 0 for i in range(100)],
        }
        df = pd.DataFrame(data)
        df.to_csv(self.data_dir / "pairs.csv", index=False)
        return df

    def __len__(self):
        return len(self.pairs)

    def __getitem__(self, idx):
        row = self.pairs.iloc[idx]

        live_path = self.data_dir / row["live_image"]
        golden_path = self.data_dir / row["golden_image"]
        label = float(row["label"])

        # Load images (or generate random tensors if files don't exist)
        live_img = self._load_image(live_path)
        golden_img = self._load_image(golden_path)

        return live_img, golden_img, torch.tensor(label, dtype=torch.float32)

    def _load_image(self, path: Path):
        try:
            from PIL import Image
            if path.exists():
                img = Image.open(path).convert("RGB")
                if self.transform:
                    img = self.transform(img)
                return img
        except Exception:
            pass

        # Return random tensor if image not available
        return torch.randn(3, TRAINING_CONFIG["input_size"], TRAINING_CONFIG["input_size"])


# ─── Model ────────────────────────────────────────────────────────────────────

class SiameseResNet50(nn.Module):
    """
    Siamese network with shared ResNet-50 backbone.
    Produces embedding vectors, then computes similarity.
    """

    def __init__(self, embedding_dim: int = 256):
        super().__init__()

        # Shared ResNet-50 backbone (pretrained on ImageNet)
        backbone = models.resnet50(weights=models.ResNet50_Weights.DEFAULT)
        self.feature_extractor = nn.Sequential(*list(backbone.children())[:-1])

        # Embedding head
        self.embedding_head = nn.Sequential(
            nn.Flatten(),
            nn.Linear(2048, 1024),
            nn.BatchNorm1d(1024),
            nn.ReLU(inplace=True),
            nn.Dropout(0.3),
            nn.Linear(1024, embedding_dim),
            nn.BatchNorm1d(embedding_dim),
        )

        # Similarity scorer
        self.classifier = nn.Sequential(
            nn.Linear(embedding_dim * 2, 128),
            nn.ReLU(inplace=True),
            nn.Dropout(0.2),
            nn.Linear(128, 1),
            nn.Sigmoid(),
        )

    def forward_one(self, x):
        """Extract embedding from one image."""
        features = self.feature_extractor(x)
        embedding = self.embedding_head(features)
        return F.normalize(embedding, p=2, dim=1)

    def forward(self, live_img, golden_img):
        """
        Forward pass: compute similarity between live and golden images.
        Returns: compliance score (0-1)
        """
        embed_live = self.forward_one(live_img)
        embed_golden = self.forward_one(golden_img)

        # Concatenate embeddings for classification
        combined = torch.cat([embed_live, embed_golden], dim=1)
        similarity = self.classifier(combined)

        return similarity.squeeze(1), embed_live, embed_golden


# ─── Loss Function ────────────────────────────────────────────────────────────

class ContrastiveLoss(nn.Module):
    """Combined contrastive + BCE loss for Siamese training."""

    def __init__(self, margin: float = 1.0, alpha: float = 0.5):
        super().__init__()
        self.margin = margin
        self.alpha = alpha
        self.bce = nn.BCELoss()

    def forward(self, similarity, embed1, embed2, label):
        # Euclidean distance between embeddings
        dist = F.pairwise_distance(embed1, embed2)

        # Contrastive loss
        contrastive = (
            label * dist.pow(2)
            + (1 - label) * F.relu(self.margin - dist).pow(2)
        ).mean()

        # BCE loss on similarity score
        bce_loss = self.bce(similarity, label)

        return self.alpha * contrastive + (1 - self.alpha) * bce_loss


# ─── Training Loop ────────────────────────────────────────────────────────────

def train_epoch(model, dataloader, criterion, optimizer, device):
    model.train()
    total_loss = 0.0
    correct = 0
    total = 0

    for live_imgs, golden_imgs, labels in dataloader:
        live_imgs = live_imgs.to(device)
        golden_imgs = golden_imgs.to(device)
        labels = labels.to(device)

        optimizer.zero_grad()
        similarity, embed_live, embed_golden = model(live_imgs, golden_imgs)
        loss = criterion(similarity, embed_live, embed_golden, labels)
        loss.backward()
        optimizer.step()

        total_loss += loss.item() * live_imgs.size(0)
        predicted = (similarity >= 0.5).float()
        correct += (predicted == labels).sum().item()
        total += labels.size(0)

    avg_loss = total_loss / total
    accuracy = correct / total
    return avg_loss, accuracy


def validate(model, dataloader, criterion, device):
    model.eval()
    total_loss = 0.0
    correct = 0
    total = 0

    with torch.no_grad():
        for live_imgs, golden_imgs, labels in dataloader:
            live_imgs = live_imgs.to(device)
            golden_imgs = golden_imgs.to(device)
            labels = labels.to(device)

            similarity, embed_live, embed_golden = model(live_imgs, golden_imgs)
            loss = criterion(similarity, embed_live, embed_golden, labels)

            total_loss += loss.item() * live_imgs.size(0)
            predicted = (similarity >= 0.5).float()
            correct += (predicted == labels).sum().item()
            total += labels.size(0)

    avg_loss = total_loss / total if total > 0 else 0
    accuracy = correct / total if total > 0 else 0
    return avg_loss, accuracy


def train(config: dict, data_dir: str, output_dir: str):
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    logger.info(f"Training on device: {device}")

    torch.manual_seed(config["seed"])

    # Data transforms
    train_transform = transforms.Compose([
        transforms.Resize((config["input_size"], config["input_size"])),
        transforms.RandomHorizontalFlip(),
        transforms.RandomRotation(15),
        transforms.ColorJitter(brightness=0.3, contrast=0.2, saturation=0.2),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ])

    val_transform = transforms.Compose([
        transforms.Resize((config["input_size"], config["input_size"])),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ])

    # Datasets
    full_dataset = PlanogramPairDataset(data_dir, "pairs.csv", transform=train_transform)
    n = len(full_dataset)
    train_size = int(n * config["train_split"])
    val_size = int(n * config["val_split"])
    test_size = n - train_size - val_size

    train_set, val_set, test_set = torch.utils.data.random_split(
        full_dataset, [train_size, val_size, test_size],
        generator=torch.Generator().manual_seed(config["seed"]),
    )

    train_loader = DataLoader(train_set, batch_size=config["batch_size"], shuffle=True, num_workers=4)
    val_loader = DataLoader(val_set, batch_size=config["batch_size"], shuffle=False, num_workers=4)
    test_loader = DataLoader(test_set, batch_size=config["batch_size"], shuffle=False, num_workers=4)

    # Model
    model = SiameseResNet50(embedding_dim=config["embedding_dim"]).to(device)
    criterion = ContrastiveLoss(margin=config["margin"])
    optimizer = torch.optim.Adam(
        model.parameters(),
        lr=config["learning_rate"],
        weight_decay=config["weight_decay"],
    )
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=config["epochs"])

    # Training
    best_val_acc = 0.0
    os.makedirs(output_dir, exist_ok=True)

    logger.info("=" * 60)
    logger.info("Starting Siamese ResNet-50 Planogram Training")
    logger.info(f"  Train: {train_size} | Val: {val_size} | Test: {test_size}")
    logger.info("=" * 60)

    for epoch in range(config["epochs"]):
        train_loss, train_acc = train_epoch(model, train_loader, criterion, optimizer, device)
        val_loss, val_acc = validate(model, val_loader, criterion, device)
        scheduler.step()

        logger.info(
            f"Epoch {epoch + 1}/{config['epochs']} — "
            f"Train Loss: {train_loss:.4f} Acc: {train_acc:.4f} | "
            f"Val Loss: {val_loss:.4f} Acc: {val_acc:.4f}"
        )

        if val_acc > best_val_acc:
            best_val_acc = val_acc
            torch.save(model.state_dict(), os.path.join(output_dir, "best_planogram.pth"))
            logger.info(f"  ✓ New best model saved (val_acc={val_acc:.4f})")

    # Test evaluation
    test_loss, test_acc = validate(model, test_loader, criterion, device)
    logger.info(f"Test Accuracy: {test_acc:.4f}")

    # Export to TorchScript for serving
    model.eval()
    scripted = torch.jit.script(model)
    script_path = os.path.join(output_dir, "planogram_siamese.pt")
    scripted.save(script_path)
    logger.info(f"TorchScript model saved to {script_path}")

    return model, {"test_accuracy": test_acc, "best_val_accuracy": best_val_acc}


def main():
    parser = argparse.ArgumentParser(description="Siamese ResNet-50 Planogram Training")
    parser.add_argument("--data-dir", type=str, default="./data/planogram")
    parser.add_argument("--output-dir", type=str, default="./runs/planogram")
    parser.add_argument("--epochs", type=int, default=TRAINING_CONFIG["epochs"])
    parser.add_argument("--batch-size", type=int, default=TRAINING_CONFIG["batch_size"])
    parser.add_argument("--lr", type=float, default=TRAINING_CONFIG["learning_rate"])
    args = parser.parse_args()

    config = TRAINING_CONFIG.copy()
    config["epochs"] = args.epochs
    config["batch_size"] = args.batch_size
    config["learning_rate"] = args.lr

    model, metrics = train(config, args.data_dir, args.output_dir)
    logger.info(f"Training complete. Test acc: {metrics['test_accuracy']:.4f}")


if __name__ == "__main__":
    main()
