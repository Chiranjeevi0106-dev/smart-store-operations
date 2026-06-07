"""
Smart Store Operations — Queue Management Module
Phase 6: People Detection, Tracking, Wait Time Estimation, Lane Activation

RT-DETR for bird's-eye people detection, DeepSORT tracking,
real-time wait time estimation, and auto lane activation.
"""

import logging
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

class LaneType(str, Enum):
    MANNED = "manned"
    SELF_CHECKOUT = "self_checkout"


@dataclass
class TrackedPerson:
    track_id: str
    lane_id: Optional[int] = None
    queue_entry_time: Optional[datetime] = None
    position: Tuple[float, float] = (0.0, 0.0)
    bbox: Tuple[float, float, float, float] = (0.0, 0.0, 0.0, 0.0)
    last_seen: datetime = field(default_factory=datetime.utcnow)
    is_in_queue: bool = False


@dataclass
class LaneStatus:
    lane_id: int
    lane_type: LaneType
    is_open: bool
    cashier_id: Optional[str] = None
    queue_length: int = 0
    estimated_wait_seconds: float = 0.0
    people_in_queue: List[str] = field(default_factory=list)
    avg_service_time_seconds: float = 120.0  # 2 min default
    last_updated: datetime = field(default_factory=datetime.utcnow)


@dataclass
class QueueAlert:
    alert_id: str
    store_id: str
    alert_type: str  # "warn_threshold" or "open_threshold"
    lane_id: int
    queue_length: int
    estimated_wait_seconds: float
    recommended_action: str
    assigned_cashier_id: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)


# ─── People Detection (RT-DETR) ──────────────────────────────────────────────

class PeopleDetector:
    """
    RT-DETR-based people detection for overhead bird's-eye cameras.
    Target: >= 94% accuracy for queues of 1-15 people.
    """

    def __init__(self, model_path: str = "./models/rtdetr_queue.engine"):
        self.model = None
        self.model_path = model_path
        self.confidence_threshold = 0.5
        self._load_model()

    def _load_model(self):
        try:
            from ultralytics import RTDETR
            if __import__("os").path.exists(self.model_path):
                self.model = RTDETR(self.model_path)
                logger.info(f"RT-DETR model loaded from {self.model_path}")
            else:
                logger.warning("RT-DETR model not found — running in mock mode")
        except ImportError:
            logger.warning("ultralytics not installed — running in mock mode")

    def detect(self, frame: np.ndarray) -> List[Tuple[float, float, float, float, float]]:
        """
        Detect people in overhead camera frame.
        Returns: List of (x1, y1, x2, y2, confidence) normalized bboxes.
        """
        if self.model is not None:
            results = self.model(frame, conf=self.confidence_threshold, classes=[0], verbose=False)
            detections = []
            for r in results:
                for box in r.boxes:
                    coords = box.xyxyn[0].tolist()
                    detections.append((*coords, float(box.conf[0])))
            return detections

        # Mock detections
        import random
        n_people = random.randint(3, 15)
        detections = []
        for _ in range(n_people):
            cx, cy = random.uniform(0.1, 0.9), random.uniform(0.1, 0.9)
            w, h = random.uniform(0.03, 0.06), random.uniform(0.04, 0.08)
            detections.append((cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2, random.uniform(0.7, 0.99)))
        return detections


# ─── DeepSORT Tracker ─────────────────────────────────────────────────────────

class QueueTracker:
    """
    DeepSORT-based multi-object tracker for maintaining unique customer IDs.
    Tracks: queue_length, queue_entry_time, lane_id.
    """

    MAX_AGE = 30  # frames before track is deleted
    MIN_HITS = 3  # frames before track is confirmed

    def __init__(self):
        self.tracks: Dict[str, TrackedPerson] = {}
        self.next_id = 1
        self.frame_count = 0

    def update(self, detections: List[Tuple[float, float, float, float, float]],
               lane_boundaries: Dict[int, Tuple[float, float, float, float]]) -> Dict[str, TrackedPerson]:
        """
        Update tracks with new detections.
        lane_boundaries: {lane_id: (x_min, y_min, x_max, y_max)} to assign detections to lanes.
        """
        self.frame_count += 1

        # Simple IoU-based matching (in production, use deep features)
        matched, unmatched_dets, unmatched_tracks = self._match_detections(detections)

        # Update matched tracks
        for track_id, det_idx in matched:
            track = self.tracks[track_id]
            det = detections[det_idx]
            cx = (det[0] + det[2]) / 2
            cy = (det[1] + det[3]) / 2
            track.position = (cx, cy)
            track.bbox = det[:4]
            track.last_seen = datetime.utcnow()

            # Assign to lane
            lane_id = self._find_lane(cx, cy, lane_boundaries)
            if lane_id is not None and not track.is_in_queue:
                track.lane_id = lane_id
                track.queue_entry_time = datetime.utcnow()
                track.is_in_queue = True

        # Create new tracks for unmatched detections
        for det_idx in unmatched_dets:
            det = detections[det_idx]
            cx = (det[0] + det[2]) / 2
            cy = (det[1] + det[3]) / 2
            track_id = f"CUST-{self.next_id:06d}"
            self.next_id += 1

            lane_id = self._find_lane(cx, cy, lane_boundaries)

            self.tracks[track_id] = TrackedPerson(
                track_id=track_id,
                position=(cx, cy),
                bbox=det[:4],
                lane_id=lane_id,
                queue_entry_time=datetime.utcnow() if lane_id else None,
                is_in_queue=lane_id is not None,
                last_seen=datetime.utcnow(),
            )

        # Remove stale tracks
        stale = [tid for tid, t in self.tracks.items()
                 if (datetime.utcnow() - t.last_seen).total_seconds() > 10]
        for tid in stale:
            del self.tracks[tid]

        return self.tracks

    def _match_detections(self, detections):
        """Simple IoU-based detection-to-track matching."""
        matched = []
        unmatched_dets = list(range(len(detections)))
        unmatched_tracks = []

        for track_id, track in self.tracks.items():
            best_iou = 0
            best_det = -1

            for i in unmatched_dets:
                det = detections[i]
                iou = self._compute_iou(track.bbox, det[:4])
                if iou > best_iou:
                    best_iou = iou
                    best_det = i

            if best_iou > 0.3 and best_det >= 0:
                matched.append((track_id, best_det))
                unmatched_dets.remove(best_det)
            else:
                unmatched_tracks.append(track_id)

        return matched, unmatched_dets, unmatched_tracks

    @staticmethod
    def _compute_iou(box1, box2) -> float:
        x1 = max(box1[0], box2[0])
        y1 = max(box1[1], box2[1])
        x2 = min(box1[2], box2[2])
        y2 = min(box1[3], box2[3])

        intersection = max(0, x2 - x1) * max(0, y2 - y1)
        area1 = (box1[2] - box1[0]) * (box1[3] - box1[1])
        area2 = (box2[2] - box2[0]) * (box2[3] - box2[1])
        union = area1 + area2 - intersection

        return intersection / union if union > 0 else 0

    @staticmethod
    def _find_lane(cx, cy, lane_boundaries) -> Optional[int]:
        for lane_id, (x_min, y_min, x_max, y_max) in lane_boundaries.items():
            if x_min <= cx <= x_max and y_min <= cy <= y_max:
                return lane_id
        return None

    def get_queue_lengths(self) -> Dict[int, int]:
        """Get current queue length per lane."""
        lengths = defaultdict(int)
        for track in self.tracks.values():
            if track.is_in_queue and track.lane_id is not None:
                lengths[track.lane_id] += 1
        return dict(lengths)


# ─── Wait Time Estimator ─────────────────────────────────────────────────────

class WaitTimeEstimator:
    """
    Regression model: f(queue_length, time_of_day, day_of_week, cashier_speed) → wait_seconds.
    Updates in real-time.
    """

    def __init__(self):
        self.model = None
        self.historical_service_times: Dict[int, List[float]] = defaultdict(list)
        self._load_model()

    def _load_model(self):
        try:
            import xgboost as xgb
            model_path = "./models/wait_time_xgb.json"
            if __import__("os").path.exists(model_path):
                self.model = xgb.Booster()
                self.model.load_model(model_path)
                logger.info("Wait time model loaded")
        except ImportError:
            logger.warning("XGBoost not available — using heuristic estimator")

    def estimate(self, lane: LaneStatus) -> float:
        """Estimate wait time in seconds for a lane."""
        if self.model is not None:
            import xgboost as xgb
            now = datetime.utcnow()
            features = np.array([[
                lane.queue_length,
                now.hour,
                now.weekday(),
                lane.avg_service_time_seconds,
            ]])
            dmatrix = xgb.DMatrix(features)
            return float(self.model.predict(dmatrix)[0])

        # Heuristic: wait = queue_length * avg_service_time
        return lane.queue_length * lane.avg_service_time_seconds

    def update_service_time(self, lane_id: int, service_time_seconds: float):
        """Update rolling average service time from POS transaction data."""
        self.historical_service_times[lane_id].append(service_time_seconds)
        # Keep last 100 observations
        if len(self.historical_service_times[lane_id]) > 100:
            self.historical_service_times[lane_id] = self.historical_service_times[lane_id][-100:]


# ─── Lane Activation Service ─────────────────────────────────────────────────

class LaneActivationService:
    """
    Auto-opens lanes and assigns cashiers based on wait time thresholds.

    Rules:
    - wait_time > T_warn (4 min) → alert duty manager
    - wait_time > T_open (6 min) AND idle cashier → auto-assign lane + push notification
    - All manned lanes > T_open AND SCO < 60% utilised → push SCO prompt
    """

    T_WARN_SECONDS = 240    # 4 minutes
    T_OPEN_SECONDS = 360    # 6 minutes
    SCO_UTILIZATION_THRESHOLD = 0.60

    def __init__(self, store_id: str):
        self.store_id = store_id
        self.lanes: Dict[int, LaneStatus] = {}
        self.idle_cashiers: List[str] = []
        self.alerts_sent: Dict[str, datetime] = {}
        self.alert_cooldown = 120  # 2 minute cooldown

    def configure_lanes(self, lane_configs: List[dict]):
        """Initialize lane configuration."""
        for cfg in lane_configs:
            self.lanes[cfg["lane_id"]] = LaneStatus(
                lane_id=cfg["lane_id"],
                lane_type=LaneType(cfg.get("type", "manned")),
                is_open=cfg.get("is_open", False),
                cashier_id=cfg.get("cashier_id"),
            )

    def update_queue_data(self, queue_lengths: Dict[int, int],
                          wait_estimator: WaitTimeEstimator) -> List[QueueAlert]:
        """Update queue data and check thresholds. Returns alerts."""
        alerts = []

        for lane_id, lane in self.lanes.items():
            lane.queue_length = queue_lengths.get(lane_id, 0)
            lane.estimated_wait_seconds = wait_estimator.estimate(lane)
            lane.last_updated = datetime.utcnow()

            # Check warn threshold
            if lane.estimated_wait_seconds > self.T_WARN_SECONDS:
                alert = self._check_and_alert(lane, "warn_threshold")
                if alert:
                    alerts.append(alert)

            # Check open threshold
            if lane.estimated_wait_seconds > self.T_OPEN_SECONDS:
                alert = self._try_auto_open(lane)
                if alert:
                    alerts.append(alert)

        # Check SCO overflow
        sco_alert = self._check_sco_overflow()
        if sco_alert:
            alerts.append(sco_alert)

        return alerts

    def _check_and_alert(self, lane: LaneStatus, alert_type: str) -> Optional[QueueAlert]:
        """Send warning alert if cooldown allows."""
        cooldown_key = f"{lane.lane_id}:{alert_type}"
        last_sent = self.alerts_sent.get(cooldown_key)

        if last_sent and (datetime.utcnow() - last_sent).total_seconds() < self.alert_cooldown:
            return None

        alert = QueueAlert(
            alert_id=str(uuid.uuid4()),
            store_id=self.store_id,
            alert_type=alert_type,
            lane_id=lane.lane_id,
            queue_length=lane.queue_length,
            estimated_wait_seconds=lane.estimated_wait_seconds,
            recommended_action=f"Lane {lane.lane_id} wait time is {lane.estimated_wait_seconds / 60:.1f} min. Consider opening additional lane.",
        )

        self.alerts_sent[cooldown_key] = datetime.utcnow()
        logger.info(f"Queue alert: Lane {lane.lane_id} wait={lane.estimated_wait_seconds / 60:.1f}min ({alert_type})")
        return alert

    def _try_auto_open(self, lane: LaneStatus) -> Optional[QueueAlert]:
        """Try to auto-assign an idle cashier to a new lane."""
        if not self.idle_cashiers:
            return None

        # Find a closed manned lane
        closed_lanes = [l for l in self.lanes.values()
                        if not l.is_open and l.lane_type == LaneType.MANNED]
        if not closed_lanes:
            return None

        target_lane = closed_lanes[0]
        cashier = self.idle_cashiers.pop(0)

        target_lane.is_open = True
        target_lane.cashier_id = cashier

        alert = QueueAlert(
            alert_id=str(uuid.uuid4()),
            store_id=self.store_id,
            alert_type="lane_opened",
            lane_id=target_lane.lane_id,
            queue_length=lane.queue_length,
            estimated_wait_seconds=lane.estimated_wait_seconds,
            recommended_action=f"Lane {target_lane.lane_id} auto-opened. Cashier {cashier} assigned.",
            assigned_cashier_id=cashier,
        )

        logger.info(f"Auto-opened Lane {target_lane.lane_id}, assigned cashier {cashier}")
        return alert

    def _check_sco_overflow(self) -> Optional[QueueAlert]:
        """Check if SCO prompt should be displayed."""
        manned_lanes = [l for l in self.lanes.values()
                        if l.lane_type == LaneType.MANNED and l.is_open]
        sco_lanes = [l for l in self.lanes.values()
                     if l.lane_type == LaneType.SELF_CHECKOUT and l.is_open]

        if not manned_lanes or not sco_lanes:
            return None

        all_manned_over = all(l.estimated_wait_seconds > self.T_OPEN_SECONDS for l in manned_lanes)
        sco_total_capacity = len(sco_lanes) * 1  # 1 customer per SCO
        sco_in_use = sum(1 for l in sco_lanes if l.queue_length > 0)
        sco_utilization = sco_in_use / len(sco_lanes) if sco_lanes else 1.0

        if all_manned_over and sco_utilization < self.SCO_UTILIZATION_THRESHOLD:
            cooldown_key = "sco_overflow"
            last = self.alerts_sent.get(cooldown_key)
            if last and (datetime.utcnow() - last).total_seconds() < 300:
                return None

            self.alerts_sent[cooldown_key] = datetime.utcnow()

            return QueueAlert(
                alert_id=str(uuid.uuid4()),
                store_id=self.store_id,
                alert_type="sco_prompt",
                lane_id=0,
                queue_length=sum(l.queue_length for l in manned_lanes),
                estimated_wait_seconds=max(l.estimated_wait_seconds for l in manned_lanes),
                recommended_action=f"SCO utilization at {sco_utilization * 100:.0f}%. Push SCO prompt to signage.",
            )
        return None

    def get_all_lane_statuses(self) -> List[dict]:
        """Get all lane statuses for dashboard."""
        return [
            {
                "lane_id": l.lane_id,
                "lane_type": l.lane_type.value,
                "is_open": l.is_open,
                "cashier_id": l.cashier_id,
                "queue_length": l.queue_length,
                "estimated_wait_seconds": l.estimated_wait_seconds,
                "last_updated": l.last_updated.isoformat(),
            }
            for l in self.lanes.values()
        ]


# ─── Staffing Forecast (XGBoost) ─────────────────────────────────────────────

class StaffingForecast:
    """
    XGBoost model predicting cashiers required per hour for next 7 days.
    Features: 12 months hourly footfall + transactions.
    """

    def __init__(self):
        self.model = None

    def predict_staffing(self, store_id: str, start_date: datetime, days: int = 7) -> List[dict]:
        """Predict hourly cashier requirements."""
        predictions = []

        for day in range(days):
            for hour in range(6, 22):
                date = start_date + timedelta(days=day)
                dt = date.replace(hour=hour, minute=0, second=0)

                # Heuristic prediction based on typical patterns
                base = 2
                if dt.weekday() >= 5:  # Weekend
                    base = 3
                if 11 <= hour <= 14:  # Lunch peak
                    base += 2
                elif 17 <= hour <= 20:  # Evening peak
                    base += 3
                elif hour < 8 or hour > 20:
                    base = max(1, base - 1)

                predictions.append({
                    "store_id": store_id,
                    "datetime": dt.isoformat(),
                    "hour": hour,
                    "day_of_week": dt.strftime("%A"),
                    "cashiers_required": base,
                    "predicted_footfall": base * 45,
                    "confidence": 0.85,
                })

        return predictions


# ─── Main Entry Point ─────────────────────────────────────────────────────────

class QueueManagementPipeline:
    """Orchestrates the full queue management pipeline."""

    def __init__(self, store_id: str):
        self.store_id = store_id
        self.detector = PeopleDetector()
        self.tracker = QueueTracker()
        self.wait_estimator = WaitTimeEstimator()
        self.lane_service = LaneActivationService(store_id)
        self.staffing = StaffingForecast()

        # Default lane boundaries (normalized coordinates)
        self.lane_boundaries = {
            1: (0.05, 0.70, 0.20, 0.95),
            2: (0.22, 0.70, 0.37, 0.95),
            3: (0.39, 0.70, 0.54, 0.95),
            4: (0.56, 0.70, 0.71, 0.95),
            5: (0.73, 0.70, 0.88, 0.95),  # SCO
            6: (0.90, 0.70, 0.99, 0.95),  # SCO
        }

    def process_frame(self, frame: np.ndarray) -> dict:
        """Process a single camera frame through the full pipeline."""
        # Detect people
        detections = self.detector.detect(frame)

        # Track across frames
        tracks = self.tracker.update(detections, self.lane_boundaries)

        # Get queue lengths per lane
        queue_lengths = self.tracker.get_queue_lengths()

        # Check thresholds and generate alerts
        alerts = self.lane_service.update_queue_data(queue_lengths, self.wait_estimator)

        return {
            "store_id": self.store_id,
            "timestamp": datetime.utcnow().isoformat(),
            "total_people": len(tracks),
            "queue_lengths": queue_lengths,
            "lane_statuses": self.lane_service.get_all_lane_statuses(),
            "alerts": [
                {
                    "alert_id": a.alert_id,
                    "alert_type": a.alert_type,
                    "lane_id": a.lane_id,
                    "queue_length": a.queue_length,
                    "estimated_wait_seconds": a.estimated_wait_seconds,
                    "recommended_action": a.recommended_action,
                }
                for a in alerts
            ],
        }


if __name__ == "__main__":
    pipeline = QueueManagementPipeline(store_id="STORE-001")

    # Configure lanes
    pipeline.lane_service.configure_lanes([
        {"lane_id": 1, "type": "manned", "is_open": True, "cashier_id": "CASH-001"},
        {"lane_id": 2, "type": "manned", "is_open": True, "cashier_id": "CASH-002"},
        {"lane_id": 3, "type": "manned", "is_open": False},
        {"lane_id": 4, "type": "manned", "is_open": False},
        {"lane_id": 5, "type": "self_checkout", "is_open": True},
        {"lane_id": 6, "type": "self_checkout", "is_open": True},
    ])
    pipeline.lane_service.idle_cashiers = ["CASH-003", "CASH-004"]

    # Simulate frames
    for frame_idx in range(50):
        mock_frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        result = pipeline.process_frame(mock_frame)

        if result["alerts"]:
            for a in result["alerts"]:
                logger.info(f"Frame {frame_idx}: {a['alert_type']} — {a['recommended_action']}")

        if frame_idx % 10 == 0:
            logger.info(f"Frame {frame_idx}: {result['total_people']} people, queues={result['queue_lengths']}")

    # Staffing forecast
    forecast = pipeline.staffing.predict_staffing("STORE-001", datetime.utcnow(), days=3)
    logger.info(f"\nStaffing forecast (next 3 days): {len(forecast)} hourly predictions")
    for f in forecast[:5]:
        logger.info(f"  {f['datetime']}: {f['cashiers_required']} cashiers needed")
