"""
Smart Store Operations — Loss Prevention Module
Phase 7: Behaviour Analytics, Dwell Anomaly, RFID Reconciliation,
         Video Clipping, Alert Dedup, Audit Trail

All inference on-device — no raw video leaves edge node.
"""

import json
import logging
import os
import time
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from collections import defaultdict
from enum import Enum

import numpy as np

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


# ─── Data Models ──────────────────────────────────────────────────────────────

class BehaviourClass(str, Enum):
    NORMAL_BROWSING = "normal_browsing"
    PROLONGED_LOITERING = "prolonged_loitering"
    CONCEALMENT_GESTURE = "concealment_gesture"
    TICKET_SWITCHING = "ticket_switching"
    NORMAL_CHECKOUT = "normal_checkout"


class AlertSeverity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class LPAlert:
    alert_id: str
    store_id: str
    zone: str
    behaviour_detected: BehaviourClass
    confidence: float
    customer_tracking_id: str
    dwell_time_seconds: Optional[float] = None
    video_clip_url: Optional[str] = None
    rfid_discrepancy: Optional[bool] = None
    severity: AlertSeverity = AlertSeverity.MEDIUM
    timestamp: datetime = field(default_factory=datetime.utcnow)
    acknowledged: bool = False
    acknowledged_by: Optional[str] = None
    acknowledged_at: Optional[datetime] = None
    action_taken: Optional[str] = None  # "acknowledge", "dismiss", "escalate"
    reason: Optional[str] = None


@dataclass
class AuditRecord:
    record_id: str
    alert_id: str
    officer_id: str
    action: str  # "acknowledge", "dismiss", "escalate", "review"
    reason: Optional[str]
    timestamp: datetime
    metadata: Optional[dict] = None


# ─── Behaviour Analytics ─────────────────────────────────────────────────────

class BehaviourAnalytics:
    """
    MediaPipe Pose skeleton extraction + temporal CNN classifier.

    Classes: {normal_browsing, prolonged_loitering, concealment_gesture,
              ticket_switching, normal_checkout}
    Target: Precision >= 0.85
    """

    SKELETON_FEATURES = 33 * 3  # 33 MediaPipe landmarks × (x,y,z)
    TEMPORAL_WINDOW = 30  # 30 frames (~1 second at 30fps)

    def __init__(self, model_path: str = "./models/behaviour_tcnn.engine"):
        self.pose_detector = None
        self.classifier = None
        self.frame_buffers: Dict[str, List[np.ndarray]] = defaultdict(list)
        self._load_models(model_path)

    def _load_models(self, model_path: str):
        try:
            import mediapipe as mp
            self.pose_detector = mp.solutions.pose.Pose(
                static_image_mode=False,
                model_complexity=1,
                min_detection_confidence=0.5,
                min_tracking_confidence=0.5,
            )
            logger.info("MediaPipe Pose loaded")
        except ImportError:
            logger.warning("MediaPipe not available — running in mock mode")

        try:
            import torch
            if os.path.exists(model_path):
                self.classifier = torch.jit.load(model_path)
                self.classifier.eval()
                logger.info(f"Behaviour classifier loaded from {model_path}")
        except (ImportError, Exception) as e:
            logger.warning(f"Behaviour classifier not available: {e}")

    def extract_skeleton(self, frame: np.ndarray, person_bbox: Tuple[float, float, float, float]) -> Optional[np.ndarray]:
        """Extract pose skeleton features for a detected person."""
        if self.pose_detector is None:
            # Mock skeleton features
            return np.random.randn(self.SKELETON_FEATURES).astype(np.float32)

        h, w = frame.shape[:2]
        x1, y1, x2, y2 = person_bbox
        x1, y1 = int(x1 * w), int(y1 * h)
        x2, y2 = int(x2 * w), int(y2 * h)

        person_crop = frame[y1:y2, x1:x2]
        if person_crop.size == 0:
            return None

        results = self.pose_detector.process(person_crop)
        if not results.pose_landmarks:
            return None

        landmarks = []
        for lm in results.pose_landmarks.landmark:
            landmarks.extend([lm.x, lm.y, lm.z])

        return np.array(landmarks, dtype=np.float32)

    def classify_behaviour(self, customer_id: str, skeleton: np.ndarray) -> Optional[Tuple[BehaviourClass, float]]:
        """Classify behaviour from temporal skeleton sequence."""
        self.frame_buffers[customer_id].append(skeleton)

        # Keep only last TEMPORAL_WINDOW frames
        if len(self.frame_buffers[customer_id]) > self.TEMPORAL_WINDOW:
            self.frame_buffers[customer_id] = self.frame_buffers[customer_id][-self.TEMPORAL_WINDOW:]

        # Need full window for classification
        if len(self.frame_buffers[customer_id]) < self.TEMPORAL_WINDOW:
            return None

        sequence = np.stack(self.frame_buffers[customer_id])

        if self.classifier is not None:
            import torch
            with torch.no_grad():
                x = torch.FloatTensor(sequence).unsqueeze(0)
                output = self.classifier(x)
                probs = torch.softmax(output, dim=1)
                pred_idx = torch.argmax(probs, dim=1).item()
                confidence = probs[0, pred_idx].item()
                return list(BehaviourClass)[pred_idx], confidence

        # Mock classification
        import random
        classes = list(BehaviourClass)
        weights = [0.60, 0.12, 0.08, 0.05, 0.15]
        predicted = random.choices(classes, weights=weights, k=1)[0]
        confidence = random.uniform(0.6, 0.98)
        return predicted, confidence


# ─── Dwell Anomaly Detection ─────────────────────────────────────────────────

class DwellAnomalyDetector:
    """
    Flags customers at high-value fixtures (jewellery, spirits, electronics)
    for > 4 min without checkout within 10 min.
    """

    DWELL_THRESHOLD_SECONDS = 240  # 4 minutes
    CHECKOUT_WINDOW_SECONDS = 600  # 10 minutes

    HIGH_VALUE_ZONES = {
        "spirits": {"x_min": 0.1, "y_min": 0.1, "x_max": 0.25, "y_max": 0.4},
        "electronics": {"x_min": 0.7, "y_min": 0.1, "x_max": 0.9, "y_max": 0.35},
        "cosmetics": {"x_min": 0.4, "y_min": 0.05, "x_max": 0.6, "y_max": 0.25},
    }

    def __init__(self):
        self.customer_dwell: Dict[str, Dict[str, datetime]] = defaultdict(dict)
        self.checkout_log: Dict[str, datetime] = {}

    def update(self, customer_id: str, position: Tuple[float, float]) -> Optional[dict]:
        """
        Update customer position and check for dwell anomaly.
        Returns alert dict if threshold exceeded.
        """
        cx, cy = position
        current_zone = self._get_zone(cx, cy)

        if current_zone:
            if current_zone not in self.customer_dwell[customer_id]:
                self.customer_dwell[customer_id][current_zone] = datetime.utcnow()
            else:
                entry_time = self.customer_dwell[customer_id][current_zone]
                dwell_seconds = (datetime.utcnow() - entry_time).total_seconds()

                if dwell_seconds >= self.DWELL_THRESHOLD_SECONDS:
                    # Check if checkout occurred
                    checkout_time = self.checkout_log.get(customer_id)
                    if checkout_time and (datetime.utcnow() - checkout_time).total_seconds() < self.CHECKOUT_WINDOW_SECONDS:
                        return None  # Customer has checked out, not suspicious

                    return {
                        "customer_id": customer_id,
                        "zone": current_zone,
                        "dwell_time_seconds": dwell_seconds,
                        "position": position,
                    }
        else:
            # Customer left high-value zone — reset dwell timers
            zones_to_clear = [z for z in self.customer_dwell[customer_id]
                              if z != current_zone]
            for z in zones_to_clear:
                if (datetime.utcnow() - self.customer_dwell[customer_id][z]).total_seconds() > 30:
                    del self.customer_dwell[customer_id][z]

        return None

    def register_checkout(self, customer_id: str):
        self.checkout_log[customer_id] = datetime.utcnow()

    def _get_zone(self, cx: float, cy: float) -> Optional[str]:
        for zone_name, bounds in self.HIGH_VALUE_ZONES.items():
            if (bounds["x_min"] <= cx <= bounds["x_max"] and
                    bounds["y_min"] <= cy <= bounds["y_max"]):
                return zone_name
        return None


# ─── RFID Exit Reconciliation ─────────────────────────────────────────────────

class RFIDReconciliationEngine:
    """
    Compares EPC reads at smart EAS gate vs POS transaction line items
    for checkouts in last 2 minutes. Discrepancy → silent alert to LP officer.
    Target: Reconciliation latency <= 8 seconds.
    """

    RECONCILIATION_WINDOW_SECONDS = 120  # 2 minutes

    def __init__(self):
        self.recent_transactions: List[dict] = []
        self.alerts_generated: List[dict] = []

    def add_pos_transaction(self, transaction: dict):
        """Record POS transaction with line items."""
        transaction["timestamp"] = datetime.utcnow()
        self.recent_transactions.append(transaction)

        # Prune old transactions
        cutoff = datetime.utcnow() - timedelta(seconds=self.RECONCILIATION_WINDOW_SECONDS * 2)
        self.recent_transactions = [t for t in self.recent_transactions if t["timestamp"] > cutoff]

    def reconcile_exit(self, gate_id: str, epc_tags_read: List[str]) -> Optional[dict]:
        """
        Reconcile EPC tags read at EAS gate with recent POS transactions.
        Returns discrepancy alert if unmatched tags found.
        """
        start_time = time.perf_counter()
        now = datetime.utcnow()

        # Find matching POS transactions in the reconciliation window
        recent_txns = [
            t for t in self.recent_transactions
            if (now - t["timestamp"]).total_seconds() <= self.RECONCILIATION_WINDOW_SECONDS
        ]

        # Get all purchased EPCs
        purchased_epcs = set()
        for txn in recent_txns:
            for item in txn.get("line_items", []):
                purchased_epcs.update(item.get("epc_tags", []))

        # Find unmatched tags
        exit_epcs = set(epc_tags_read)
        unmatched = exit_epcs - purchased_epcs
        matched = exit_epcs & purchased_epcs

        reconciliation_time_sec = time.perf_counter() - start_time

        result = {
            "gate_id": gate_id,
            "timestamp": now.isoformat(),
            "total_tags_read": len(exit_epcs),
            "matched_tags": len(matched),
            "unmatched_tags": len(unmatched),
            "unmatched_epcs": list(unmatched),
            "reconciliation_time_ms": round(reconciliation_time_sec * 1000, 1),
            "is_discrepancy": len(unmatched) > 0,
        }

        if result["is_discrepancy"]:
            logger.warning(
                f"RFID DISCREPANCY at {gate_id}: "
                f"{len(unmatched)} unmatched tags out of {len(exit_epcs)} read"
            )
            self.alerts_generated.append(result)

        return result if result["is_discrepancy"] else None


# ─── Video Clip Service ───────────────────────────────────────────────────────

class VideoClipService:
    """
    On alert trigger, extract 30s pre + 30s post clip.
    Transcode to H.264 720p. Store with 90-day retention.
    """

    PRE_SECONDS = 30
    POST_SECONDS = 30
    OUTPUT_RESOLUTION = (1280, 720)
    RETENTION_DAYS = 90

    def __init__(self, buffer_dir: str = "./video_buffer", output_dir: str = "./video_clips"):
        self.buffer_dir = buffer_dir
        self.output_dir = output_dir
        os.makedirs(self.buffer_dir, exist_ok=True)
        os.makedirs(self.output_dir, exist_ok=True)

    def extract_clip(self, camera_id: str, alert_timestamp: datetime, alert_id: str) -> Optional[str]:
        """Extract video clip around alert timestamp."""
        clip_filename = f"clip_{alert_id[:8]}_{camera_id}_{alert_timestamp.strftime('%Y%m%d_%H%M%S')}.mp4"
        clip_path = os.path.join(self.output_dir, clip_filename)

        try:
            import cv2

            # In production: read from rolling buffer or NVR
            fourcc = cv2.VideoWriter_fourcc(*"mp4v")
            writer = cv2.VideoWriter(clip_path, fourcc, 30, self.OUTPUT_RESOLUTION)

            # Mock: write blank frames
            total_frames = (self.PRE_SECONDS + self.POST_SECONDS) * 30
            for _ in range(total_frames):
                frame = np.zeros((*self.OUTPUT_RESOLUTION[::-1], 3), dtype=np.uint8)
                writer.write(frame)

            writer.release()
            logger.info(f"Video clip saved: {clip_path} ({self.PRE_SECONDS + self.POST_SECONDS}s)")
            return clip_path

        except ImportError:
            logger.warning("OpenCV not available — clip extraction skipped")
            # Create placeholder
            with open(clip_path + ".placeholder", "w") as f:
                f.write(json.dumps({
                    "alert_id": alert_id,
                    "camera_id": camera_id,
                    "start_time": (alert_timestamp - timedelta(seconds=self.PRE_SECONDS)).isoformat(),
                    "end_time": (alert_timestamp + timedelta(seconds=self.POST_SECONDS)).isoformat(),
                    "status": "pending_extraction",
                }))
            return clip_path + ".placeholder"

    def cleanup_expired(self):
        """Delete clips older than retention period."""
        cutoff = datetime.utcnow() - timedelta(days=self.RETENTION_DAYS)
        for filename in os.listdir(self.output_dir):
            filepath = os.path.join(self.output_dir, filename)
            if os.path.isfile(filepath):
                mod_time = datetime.fromtimestamp(os.path.getmtime(filepath))
                if mod_time < cutoff:
                    os.remove(filepath)
                    logger.info(f"Expired clip deleted: {filename}")


# ─── Alert Deduplication ──────────────────────────────────────────────────────

class AlertDeduplicator:
    """
    5-minute cooldown per customer_id per alert_type to prevent alert flooding.
    """

    COOLDOWN_SECONDS = 300  # 5 minutes

    def __init__(self):
        self.cooldown_map: Dict[str, datetime] = {}
        self.deduplicated_count = 0

    def should_alert(self, customer_id: str, alert_type: str) -> bool:
        """Check if alert should be generated (not in cooldown)."""
        key = f"{customer_id}:{alert_type}"
        last_alert = self.cooldown_map.get(key)

        if last_alert and (datetime.utcnow() - last_alert).total_seconds() < self.COOLDOWN_SECONDS:
            self.deduplicated_count += 1
            return False

        self.cooldown_map[key] = datetime.utcnow()
        return True

    def cleanup(self):
        """Remove expired cooldown entries."""
        cutoff = datetime.utcnow() - timedelta(seconds=self.COOLDOWN_SECONDS)
        self.cooldown_map = {k: v for k, v in self.cooldown_map.items() if v > cutoff}


# ─── Audit Trail ──────────────────────────────────────────────────────────────

class AuditTrail:
    """
    Immutable append-only audit log for LP alerts and actions.
    In production: writes to TimescaleDB append-only hypertable.
    """

    def __init__(self):
        self.records: List[AuditRecord] = []
        self.db_connection = None

    def log_action(self, alert_id: str, officer_id: str, action: str,
                   reason: str = None, metadata: dict = None) -> AuditRecord:
        """Log an action to the immutable audit trail."""
        record = AuditRecord(
            record_id=str(uuid.uuid4()),
            alert_id=alert_id,
            officer_id=officer_id,
            action=action,
            reason=reason,
            timestamp=datetime.utcnow(),
            metadata=metadata,
        )

        self.records.append(record)

        # In production: INSERT INTO lp_audit_trail (immutable, no UPDATE/DELETE)
        self._persist_record(record)

        logger.info(f"Audit: [{action}] alert={alert_id[:8]} by={officer_id} reason={reason}")
        return record

    def _persist_record(self, record: AuditRecord):
        """Persist to TimescaleDB (or local file for offline)."""
        if self.db_connection:
            # INSERT INTO lp_audit_trail (record_id, alert_id, officer_id, action, reason, timestamp, metadata)
            # VALUES (...)
            pass
        else:
            # Local file fallback
            log_path = "./data/lp_audit_trail.jsonl"
            os.makedirs(os.path.dirname(log_path), exist_ok=True)
            with open(log_path, "a") as f:
                f.write(json.dumps({
                    "record_id": record.record_id,
                    "alert_id": record.alert_id,
                    "officer_id": record.officer_id,
                    "action": record.action,
                    "reason": record.reason,
                    "timestamp": record.timestamp.isoformat(),
                    "metadata": record.metadata,
                }) + "\n")

    def get_alert_history(self, alert_id: str) -> List[AuditRecord]:
        return [r for r in self.records if r.alert_id == alert_id]

    def get_officer_actions(self, officer_id: str, since: datetime = None) -> List[AuditRecord]:
        records = [r for r in self.records if r.officer_id == officer_id]
        if since:
            records = [r for r in records if r.timestamp >= since]
        return records


# ─── LP Pipeline Orchestrator ─────────────────────────────────────────────────

class LossPreventionPipeline:
    """Orchestrates the full LP module."""

    def __init__(self, store_id: str):
        self.store_id = store_id
        self.behaviour = BehaviourAnalytics()
        self.dwell_detector = DwellAnomalyDetector()
        self.rfid_reconciliation = RFIDReconciliationEngine()
        self.video_clipper = VideoClipService()
        self.deduplicator = AlertDeduplicator()
        self.audit_trail = AuditTrail()
        self.active_alerts: Dict[str, LPAlert] = {}

    def process_frame(self, frame: np.ndarray, tracked_persons: Dict[str, dict]) -> List[LPAlert]:
        """Process a frame through all LP analytics."""
        alerts = []

        for customer_id, person in tracked_persons.items():
            bbox = person.get("bbox", (0, 0, 1, 1))
            position = person.get("position", (0.5, 0.5))

            # Behaviour analysis
            skeleton = self.behaviour.extract_skeleton(frame, bbox)
            if skeleton is not None:
                result = self.behaviour.classify_behaviour(customer_id, skeleton)
                if result:
                    behaviour, confidence = result
                    if behaviour not in (BehaviourClass.NORMAL_BROWSING, BehaviourClass.NORMAL_CHECKOUT):
                        if confidence >= 0.85 and self.deduplicator.should_alert(customer_id, behaviour.value):
                            alert = self._create_alert(
                                customer_id=customer_id,
                                behaviour=behaviour,
                                confidence=confidence,
                                zone=self._get_zone_name(position),
                            )
                            alerts.append(alert)

            # Dwell anomaly
            dwell_result = self.dwell_detector.update(customer_id, position)
            if dwell_result:
                if self.deduplicator.should_alert(customer_id, "dwell_anomaly"):
                    alert = self._create_alert(
                        customer_id=customer_id,
                        behaviour=BehaviourClass.PROLONGED_LOITERING,
                        confidence=0.90,
                        zone=dwell_result["zone"],
                        dwell_time=dwell_result["dwell_time_seconds"],
                    )
                    alerts.append(alert)

        return alerts

    def reconcile_exit(self, gate_id: str, epc_tags: List[str]) -> Optional[LPAlert]:
        """Reconcile RFID at exit gate."""
        discrepancy = self.rfid_reconciliation.reconcile_exit(gate_id, epc_tags)
        if discrepancy:
            alert = LPAlert(
                alert_id=str(uuid.uuid4()),
                store_id=self.store_id,
                zone=f"exit_{gate_id}",
                behaviour_detected=BehaviourClass.NORMAL_BROWSING,
                confidence=0.95,
                customer_tracking_id="unknown",
                rfid_discrepancy=True,
                severity=AlertSeverity.HIGH,
            )
            self.active_alerts[alert.alert_id] = alert
            self.audit_trail.log_action(alert.alert_id, "SYSTEM", "created",
                                        f"RFID discrepancy: {discrepancy['unmatched_tags']} unmatched tags")
            return alert
        return None

    def acknowledge_alert(self, alert_id: str, officer_id: str, action: str, reason: str = None):
        """LP officer acknowledges/dismisses/escalates an alert."""
        if alert_id not in self.active_alerts:
            return None

        alert = self.active_alerts[alert_id]
        alert.acknowledged = True
        alert.acknowledged_by = officer_id
        alert.acknowledged_at = datetime.utcnow()
        alert.action_taken = action
        alert.reason = reason

        self.audit_trail.log_action(alert_id, officer_id, action, reason)
        return alert

    def _create_alert(self, customer_id: str, behaviour: BehaviourClass,
                      confidence: float, zone: str, dwell_time: float = None) -> LPAlert:
        """Create and store LP alert with video clip."""
        alert = LPAlert(
            alert_id=str(uuid.uuid4()),
            store_id=self.store_id,
            zone=zone,
            behaviour_detected=behaviour,
            confidence=confidence,
            customer_tracking_id=customer_id,
            dwell_time_seconds=dwell_time,
            severity=self._determine_severity(behaviour, confidence),
        )

        # Extract video clip
        clip_path = self.video_clipper.extract_clip(
            camera_id=f"CAM-{zone}",
            alert_timestamp=alert.timestamp,
            alert_id=alert.alert_id,
        )
        alert.video_clip_url = clip_path

        self.active_alerts[alert.alert_id] = alert
        self.audit_trail.log_action(alert.alert_id, "SYSTEM", "created",
                                    f"{behaviour.value} detected (conf={confidence:.2f})")

        logger.warning(
            f"LP ALERT [{alert.alert_id[:8]}]: {behaviour.value} "
            f"customer={customer_id} zone={zone} conf={confidence:.2f}"
        )
        return alert

    @staticmethod
    def _determine_severity(behaviour: BehaviourClass, confidence: float) -> AlertSeverity:
        if behaviour == BehaviourClass.CONCEALMENT_GESTURE and confidence >= 0.9:
            return AlertSeverity.CRITICAL
        elif behaviour in (BehaviourClass.CONCEALMENT_GESTURE, BehaviourClass.TICKET_SWITCHING):
            return AlertSeverity.HIGH
        elif behaviour == BehaviourClass.PROLONGED_LOITERING:
            return AlertSeverity.MEDIUM
        return AlertSeverity.LOW

    @staticmethod
    def _get_zone_name(position: Tuple[float, float]) -> str:
        cx, cy = position
        if cx < 0.33:
            return "zone_A" if cy < 0.5 else "zone_D"
        elif cx < 0.66:
            return "zone_B" if cy < 0.5 else "zone_E"
        else:
            return "zone_C" if cy < 0.5 else "zone_F"


# ─── Main ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import random

    pipeline = LossPreventionPipeline(store_id="STORE-001")

    # Simulate POS transactions for RFID reconciliation
    pipeline.rfid_reconciliation.add_pos_transaction({
        "transaction_id": "TXN-001",
        "line_items": [
            {"sku": "SKU-001", "epc_tags": ["EPC-A1", "EPC-A2"]},
            {"sku": "SKU-002", "epc_tags": ["EPC-B1"]},
        ],
    })

    # Simulate RFID exit reconciliation
    result = pipeline.reconcile_exit("GATE-1", ["EPC-A1", "EPC-A2", "EPC-B1", "EPC-C1"])
    if result:
        logger.info(f"RFID alert created: {result.alert_id[:8]}")

    # Simulate frame processing
    for frame_idx in range(60):
        mock_frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        
        tracked = {
            f"CUST-{i:03d}": {
                "bbox": (random.uniform(0, 0.4), random.uniform(0, 0.4),
                         random.uniform(0.5, 0.9), random.uniform(0.5, 0.9)),
                "position": (random.uniform(0.1, 0.9), random.uniform(0.1, 0.9)),
            }
            for i in range(random.randint(3, 8))
        }

        alerts = pipeline.process_frame(mock_frame, tracked)
        for alert in alerts:
            # Simulate LP officer response
            if random.random() > 0.5:
                pipeline.acknowledge_alert(
                    alert.alert_id,
                    officer_id="LP-001",
                    action=random.choice(["acknowledge", "dismiss", "escalate"]),
                    reason="Reviewed footage",
                )

    logger.info(f"\nActive alerts: {len(pipeline.active_alerts)}")
    logger.info(f"Audit records: {len(pipeline.audit_trail.records)}")
    logger.info(f"Deduplicated alerts: {pipeline.deduplicator.deduplicated_count}")
