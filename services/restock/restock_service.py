"""
Smart Store Operations — LSTM Restock Prediction + RestockTask Service
Phase 5: Sensor Fusion & Replenishment Engine

Predicts time-to-stockout per SKU using LSTM on hourly sales velocity + ShelfState.
Target: MAE <= 15 minutes for peak hours.
"""

import json
import logging
import os
import uuid
from datetime import datetime, timedelta
from typing import List, Optional, Dict
from dataclasses import dataclass, asdict

import numpy as np

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


# ─── Model Configuration ─────────────────────────────────────────────────────

LSTM_CONFIG = {
    "input_features": [
        "hourly_sales_velocity",
        "current_stock_level",
        "weight_ratio",
        "rfid_tag_ratio",
        "fused_confidence",
        "hour_of_day",
        "day_of_week",
        "is_promotion",
        "avg_daily_sales_30d",
        "shelf_capacity",
    ],
    "sequence_length": 24,  # 24 hours of hourly data
    "hidden_size": 128,
    "num_layers": 2,
    "dropout": 0.2,
    "output_size": 1,  # predicted minutes to stockout
    "batch_size": 64,
    "epochs": 100,
    "learning_rate": 0.001,
    "target_mae_minutes": 15,
}


# ─── LSTM Model ───────────────────────────────────────────────────────────────

class StockoutLSTM:
    """LSTM model for predicting time-to-stockout per SKU."""

    def __init__(self, config: dict = None):
        self.config = config or LSTM_CONFIG
        self.model = None
        self.scaler = None
        self._build_model()

    def _build_model(self):
        try:
            import torch
            import torch.nn as nn

            class LSTMPredictor(nn.Module):
                def __init__(self, input_size, hidden_size, num_layers, dropout, output_size):
                    super().__init__()
                    self.lstm = nn.LSTM(
                        input_size=input_size,
                        hidden_size=hidden_size,
                        num_layers=num_layers,
                        dropout=dropout,
                        batch_first=True,
                        bidirectional=False,
                    )
                    self.attention = nn.Sequential(
                        nn.Linear(hidden_size, hidden_size // 2),
                        nn.Tanh(),
                        nn.Linear(hidden_size // 2, 1),
                    )
                    self.fc = nn.Sequential(
                        nn.Linear(hidden_size, 64),
                        nn.ReLU(),
                        nn.Dropout(0.1),
                        nn.Linear(64, output_size),
                        nn.ReLU(),  # Output is minutes (non-negative)
                    )

                def forward(self, x):
                    lstm_out, _ = self.lstm(x)
                    # Attention mechanism
                    attn_weights = torch.softmax(self.attention(lstm_out), dim=1)
                    context = torch.sum(attn_weights * lstm_out, dim=1)
                    output = self.fc(context)
                    return output.squeeze(-1)

            self.model = LSTMPredictor(
                input_size=len(self.config["input_features"]),
                hidden_size=self.config["hidden_size"],
                num_layers=self.config["num_layers"],
                dropout=self.config["dropout"],
                output_size=self.config["output_size"],
            )
            logger.info("LSTM model built successfully")

        except ImportError:
            logger.warning("PyTorch not available — running in mock prediction mode")
            self.model = None

    def train_model(self, train_data: np.ndarray, train_labels: np.ndarray,
                    val_data: np.ndarray, val_labels: np.ndarray):
        """Train the LSTM model."""
        if self.model is None:
            logger.warning("No model available for training")
            return {"train_mae": 0, "val_mae": 0}

        import torch
        from torch.utils.data import TensorDataset, DataLoader

        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model = self.model.to(device)

        train_dataset = TensorDataset(
            torch.FloatTensor(train_data),
            torch.FloatTensor(train_labels),
        )
        val_dataset = TensorDataset(
            torch.FloatTensor(val_data),
            torch.FloatTensor(val_labels),
        )

        train_loader = DataLoader(train_dataset, batch_size=self.config["batch_size"], shuffle=True)
        val_loader = DataLoader(val_dataset, batch_size=self.config["batch_size"])

        optimizer = torch.optim.Adam(self.model.parameters(), lr=self.config["learning_rate"])
        scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(optimizer, patience=10, factor=0.5)
        criterion = torch.nn.L1Loss()  # MAE loss

        best_val_mae = float("inf")

        for epoch in range(self.config["epochs"]):
            # Train
            self.model.train()
            train_loss = 0
            for batch_x, batch_y in train_loader:
                batch_x, batch_y = batch_x.to(device), batch_y.to(device)
                optimizer.zero_grad()
                pred = self.model(batch_x)
                loss = criterion(pred, batch_y)
                loss.backward()
                torch.nn.utils.clip_grad_norm_(self.model.parameters(), max_norm=1.0)
                optimizer.step()
                train_loss += loss.item() * batch_x.size(0)

            # Validate
            self.model.eval()
            val_loss = 0
            with torch.no_grad():
                for batch_x, batch_y in val_loader:
                    batch_x, batch_y = batch_x.to(device), batch_y.to(device)
                    pred = self.model(batch_x)
                    val_loss += criterion(pred, batch_y).item() * batch_x.size(0)

            train_mae = train_loss / len(train_dataset)
            val_mae = val_loss / len(val_dataset)
            scheduler.step(val_mae)

            if (epoch + 1) % 10 == 0:
                logger.info(f"Epoch {epoch + 1}/{self.config['epochs']} — "
                           f"Train MAE: {train_mae:.2f} min | Val MAE: {val_mae:.2f} min")

            if val_mae < best_val_mae:
                best_val_mae = val_mae
                torch.save(self.model.state_dict(), "best_stockout_lstm.pth")

        logger.info(f"Training complete. Best Val MAE: {best_val_mae:.2f} min")
        target = self.config["target_mae_minutes"]
        if best_val_mae <= target:
            logger.info(f"✓ Target MAE <= {target} min ACHIEVED")
        else:
            logger.warning(f"✗ Target MAE <= {target} min NOT MET ({best_val_mae:.2f})")

        return {"train_mae": train_mae, "val_mae": best_val_mae}

    def predict(self, sequence: np.ndarray) -> float:
        """Predict time-to-stockout in minutes."""
        if self.model is None:
            # Mock prediction
            return float(np.random.uniform(10, 180))

        import torch
        self.model.eval()
        with torch.no_grad():
            x = torch.FloatTensor(sequence).unsqueeze(0)
            pred = self.model(x)
            return float(pred.item())


# ─── Restock Task Service ─────────────────────────────────────────────────────

@dataclass
class RestockTask:
    task_id: str
    store_id: str
    aisle: str
    bay: int
    shelf_level: int
    product_id: str
    sku_code: str
    product_name: str
    current_quantity_estimate: int
    restock_quantity: int
    priority: str  # "urgent", "normal", "low"
    fused_confidence: float
    predicted_stockout_time_min: float
    assigned_to: Optional[str] = None
    created_at: str = ""
    due_by: Optional[str] = None
    completed_at: Optional[str] = None
    status: str = "pending"


class RestockService:
    """
    Generates RestockTask events based on LSTM predictions + ShelfState.

    Trigger logic:
    - If predicted_time_to_stockout <= 45 min AND within shift hours → generate task
    - Priority: urgent (<=15min), normal (15-30min), low (30-45min)
    """

    STOCKOUT_THRESHOLD_MIN = 45
    SHIFT_HOURS = (6, 22)  # 6 AM to 10 PM

    PRIORITY_THRESHOLDS = {
        "urgent": 15,
        "normal": 30,
        "low": 45,
    }

    AUTO_DISPATCH_CONFIDENCE = 0.95
    HUMAN_REVIEW_MIN_CONFIDENCE = 0.70

    def __init__(self, lstm_model: StockoutLSTM):
        self.lstm = lstm_model
        self.pending_tasks: Dict[str, RestockTask] = {}
        self.task_history: List[RestockTask] = []

    def evaluate_shelf_state(self, shelf_state: dict) -> Optional[RestockTask]:
        """Evaluate a ShelfState event and generate RestockTask if needed."""
        if not shelf_state.get("is_out_of_stock", False):
            return None

        current_hour = datetime.utcnow().hour
        if not (self.SHIFT_HOURS[0] <= current_hour <= self.SHIFT_HOURS[1]):
            logger.debug("Outside shift hours — suppressing restock task")
            return None

        # Get prediction from LSTM
        predicted_min = shelf_state.get("predicted_stockout_time_min")
        if predicted_min is None:
            # Use mock sequence for prediction
            predicted_min = self.lstm.predict(np.random.randn(24, len(LSTM_CONFIG["input_features"])))

        if predicted_min > self.STOCKOUT_THRESHOLD_MIN:
            return None

        # Determine priority
        priority = "low"
        for p, threshold in sorted(self.PRIORITY_THRESHOLDS.items(), key=lambda x: x[1]):
            if predicted_min <= threshold:
                priority = p
                break

        # Check deduplication — don't create duplicate tasks
        dedup_key = f"{shelf_state['store_id']}:{shelf_state['aisle']}:{shelf_state['bay']}:{shelf_state['product_id']}"
        if dedup_key in self.pending_tasks:
            existing = self.pending_tasks[dedup_key]
            if existing.status == "pending":
                # Update priority if escalated
                if self.PRIORITY_THRESHOLDS.get(priority, 99) < self.PRIORITY_THRESHOLDS.get(existing.priority, 99):
                    existing.priority = priority
                    logger.info(f"Task {existing.task_id[:8]} escalated to {priority}")
                return None

        now = datetime.utcnow()
        task = RestockTask(
            task_id=str(uuid.uuid4()),
            store_id=shelf_state["store_id"],
            aisle=shelf_state["aisle"],
            bay=shelf_state["bay"],
            shelf_level=shelf_state.get("shelf_level", 0),
            product_id=shelf_state["product_id"],
            sku_code=shelf_state.get("sku_code", shelf_state["product_id"]),
            product_name=shelf_state.get("product_name", "Unknown Product"),
            current_quantity_estimate=max(0, int(shelf_state.get("rfid_tag_count", 0))),
            restock_quantity=shelf_state.get("shelf_capacity", 10),
            priority=priority,
            fused_confidence=shelf_state["fused_confidence"],
            predicted_stockout_time_min=predicted_min,
            created_at=now.isoformat(),
            due_by=(now + timedelta(minutes=predicted_min * 0.8)).isoformat(),
            status="pending",
        )

        self.pending_tasks[dedup_key] = task

        # Auto-dispatch or human review
        if task.fused_confidence >= self.AUTO_DISPATCH_CONFIDENCE:
            task.status = "auto_dispatched"
            logger.info(f"RestockTask AUTO-DISPATCHED [{task.task_id[:8]}]: "
                        f"{task.aisle}/Bay-{task.bay} {task.product_id} "
                        f"priority={task.priority} est={predicted_min:.0f}min")
        elif task.fused_confidence >= self.HUMAN_REVIEW_MIN_CONFIDENCE:
            task.status = "pending_review"
            logger.info(f"RestockTask PENDING REVIEW [{task.task_id[:8]}]: "
                        f"{task.aisle}/Bay-{task.bay} {task.product_id} "
                        f"priority={task.priority} conf={task.fused_confidence:.2f}")
        else:
            logger.debug(f"Low confidence ({task.fused_confidence:.2f}) — task suppressed")
            return None

        return task

    def complete_task(self, task_id: str, completed_by: str, photo_url: str = None) -> Optional[RestockTask]:
        """Mark a task as completed (from staff handheld app)."""
        for key, task in self.pending_tasks.items():
            if task.task_id == task_id:
                task.status = "completed"
                task.completed_at = datetime.utcnow().isoformat()
                task.assigned_to = completed_by
                self.task_history.append(task)
                del self.pending_tasks[key]

                # Calculate actual vs predicted restock time
                created = datetime.fromisoformat(task.created_at)
                completed = datetime.fromisoformat(task.completed_at)
                actual_response_min = (completed - created).total_seconds() / 60

                logger.info(
                    f"Task completed [{task_id[:8]}]: "
                    f"predicted={task.predicted_stockout_time_min:.0f}min "
                    f"actual_response={actual_response_min:.0f}min"
                )
                return task
        return None


# ─── WMS Integration ──────────────────────────────────────────────────────────

class WMSIntegration:
    """
    Publishes RestockTask events to WMS via REST webhook.
    Maps internal SKU IDs to WMS product codes.
    Retry on 5xx with exponential backoff.
    """

    def __init__(self, wms_url: str = "http://wms.local/api/v1/restock",
                 api_key: str = "", max_retries: int = 5):
        self.wms_url = wms_url
        self.api_key = api_key
        self.max_retries = max_retries
        self.sku_mapping: Dict[str, str] = {}  # internal_id -> wms_code

    def load_sku_mapping(self, mapping_file: str):
        """Load SKU mapping from JSON file."""
        if os.path.exists(mapping_file):
            with open(mapping_file) as f:
                self.sku_mapping = json.load(f)
            logger.info(f"Loaded {len(self.sku_mapping)} SKU mappings")
        else:
            logger.warning(f"SKU mapping file not found: {mapping_file}")

    def send_restock_task(self, task: RestockTask) -> bool:
        """Send RestockTask to WMS with retry logic."""
        wms_code = self.sku_mapping.get(task.product_id, task.sku_code)

        payload = {
            "external_task_id": task.task_id,
            "wms_product_code": wms_code,
            "store_id": task.store_id,
            "location": f"{task.aisle}-Bay{task.bay}-L{task.shelf_level}",
            "quantity": task.restock_quantity,
            "priority": task.priority,
            "due_by": task.due_by,
        }

        for attempt in range(self.max_retries):
            try:
                import requests
                response = requests.post(
                    self.wms_url,
                    json=payload,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                    timeout=10,
                )

                if response.status_code < 300:
                    logger.info(f"WMS task sent: {task.task_id[:8]} → {wms_code}")
                    return True
                elif response.status_code >= 500:
                    wait = 2 ** attempt
                    logger.warning(f"WMS 5xx error (attempt {attempt + 1}), retrying in {wait}s...")
                    import time
                    time.sleep(wait)
                else:
                    logger.error(f"WMS rejected task: {response.status_code} — {response.text}")
                    return False

            except ImportError:
                logger.info(f"WMS task (mock): {task.task_id[:8]} → {wms_code} — {payload}")
                return True
            except Exception as e:
                wait = 2 ** attempt
                logger.error(f"WMS error (attempt {attempt + 1}): {e}, retrying in {wait}s...")
                import time
                time.sleep(wait)

        logger.error(f"WMS task failed after {self.max_retries} attempts: {task.task_id[:8]}")
        return False


# ─── Feedback Loop ────────────────────────────────────────────────────────────

class FeedbackLoop:
    """
    When staff marks task complete → update ShelfState →
    measure actual vs predicted restock time → feed delta to LSTM retraining.
    """

    def __init__(self):
        self.feedback_records: List[dict] = []

    def record_completion(self, task: RestockTask):
        """Record task completion for LSTM feedback."""
        if not task.completed_at or not task.created_at:
            return

        created = datetime.fromisoformat(task.created_at)
        completed = datetime.fromisoformat(task.completed_at)
        actual_response_min = (completed - created).total_seconds() / 60
        predicted = task.predicted_stockout_time_min

        delta = actual_response_min - predicted

        record = {
            "task_id": task.task_id,
            "store_id": task.store_id,
            "product_id": task.product_id,
            "predicted_stockout_min": predicted,
            "actual_response_min": actual_response_min,
            "delta_min": delta,
            "priority": task.priority,
            "fused_confidence": task.fused_confidence,
            "timestamp": datetime.utcnow().isoformat(),
        }

        self.feedback_records.append(record)
        logger.info(f"Feedback recorded: predicted={predicted:.0f}min actual={actual_response_min:.0f}min delta={delta:+.0f}min")

        # Check if retraining is needed
        if len(self.feedback_records) >= 100:
            self._check_retrain_trigger()

    def _check_retrain_trigger(self):
        """Check if model should be retrained based on feedback."""
        recent = self.feedback_records[-100:]
        mae = np.mean([abs(r["delta_min"]) for r in recent])

        if mae > LSTM_CONFIG["target_mae_minutes"]:
            logger.warning(f"LSTM MAE degraded to {mae:.1f}min (target={LSTM_CONFIG['target_mae_minutes']}min)")
            logger.warning("→ Triggering LSTM retraining pipeline")
            # In production: trigger Airflow DAG for retraining
            return True
        return False

    def get_performance_stats(self) -> dict:
        """Get LSTM prediction performance statistics."""
        if not self.feedback_records:
            return {"mae": 0, "records": 0}

        deltas = [abs(r["delta_min"]) for r in self.feedback_records]
        return {
            "mae": float(np.mean(deltas)),
            "median_ae": float(np.median(deltas)),
            "p95_ae": float(np.percentile(deltas, 95)),
            "records": len(self.feedback_records),
            "within_target": sum(1 for d in deltas if d <= LSTM_CONFIG["target_mae_minutes"]) / len(deltas),
        }


# ─── Main ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Restock Prediction & Task Service")
    parser.add_argument("--mode", choices=["train", "serve", "simulate"], default="simulate")
    args = parser.parse_args()

    lstm = StockoutLSTM()
    restock_service = RestockService(lstm)
    wms = WMSIntegration()
    feedback = FeedbackLoop()

    if args.mode == "simulate":
        logger.info("Running restock service simulation...")
        import random

        for i in range(20):
            shelf_state = {
                "store_id": "STORE-001",
                "aisle": random.choice(["A1", "A2", "B1", "B2"]),
                "bay": random.randint(1, 8),
                "shelf_level": random.randint(0, 3),
                "product_id": f"PROD-{random.randint(1, 50):03d}",
                "sku_code": f"SKU-{random.randint(1000, 9999)}",
                "product_name": f"Product {random.randint(1, 50)}",
                "fused_confidence": random.uniform(0.6, 0.99),
                "is_out_of_stock": True,
                "rfid_tag_count": random.randint(0, 3),
                "shelf_capacity": random.randint(8, 20),
            }

            task = restock_service.evaluate_shelf_state(shelf_state)
            if task:
                wms.send_restock_task(task)
                # Simulate completion
                if random.random() > 0.3:
                    task_result = restock_service.complete_task(
                        task.task_id, completed_by="STAFF-001"
                    )
                    if task_result:
                        feedback.record_completion(task_result)

        stats = feedback.get_performance_stats()
        logger.info(f"Feedback stats: {stats}")
