"""
Smart Store Operations — MQTT Alert Publisher
Phase 4: Computer Vision Pipeline

Handles MQTT publishing of OOS alerts with deduplication and consecutive-frame logic.
Topic: stores/{store_id}/shelf/oos
"""

import json
import logging
import time
import uuid
from datetime import datetime
from collections import defaultdict
from typing import Optional, Dict

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


class OOSAlertPublisher:
    """
    Manages out-of-stock alert publishing via MQTT.

    Alert logic:
    - If empty_facing confidence >= 0.85 for >= 3 consecutive frames
    - Publish to stores/{store_id}/shelf/oos with QoS 2
    - 5-minute cooldown per product per bay to prevent alert flooding
    """

    ALERT_CONFIDENCE_THRESHOLD = 0.85
    CONSECUTIVE_FRAME_THRESHOLD = 3
    COOLDOWN_SECONDS = 300  # 5-minute cooldown per alert

    def __init__(self, mqtt_client=None, store_id: str = "STORE-001"):
        self.mqtt_client = mqtt_client
        self.store_id = store_id

        # Tracking: camera_id -> facing_key -> consecutive_count
        self.consecutive_tracker: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))

        # Cooldown: facing_key -> last_alert_timestamp
        self.cooldown_tracker: Dict[str, float] = {}

        # Stats
        self.alerts_published = 0
        self.alerts_suppressed = 0

    def process_frame_detections(self, camera_id: str, detections: list, aisle: str = None, bay: int = None):
        """
        Process detections from a single frame and trigger alerts if conditions met.

        Args:
            camera_id: Unique camera identifier
            detections: List of Detection objects from YOLO inference
            aisle: Aisle identifier
            bay: Bay number
        """
        current_empty_keys = set()

        for det in detections:
            if det.get("class_name") == "empty_facing" and det.get("confidence", 0) >= self.ALERT_CONFIDENCE_THRESHOLD:
                facing_key = self._make_facing_key(
                    aisle or det.get("aisle", "unknown"),
                    bay if bay is not None else det.get("bay", 0),
                    det.get("product_id", "unknown"),
                    det.get("shelf_level", 0),
                )
                current_empty_keys.add(facing_key)

                # Increment consecutive counter
                self.consecutive_tracker[camera_id][facing_key] += 1
                count = self.consecutive_tracker[camera_id][facing_key]

                if count >= self.CONSECUTIVE_FRAME_THRESHOLD:
                    if self._can_alert(facing_key):
                        self._publish_alert(
                            camera_id=camera_id,
                            facing_key=facing_key,
                            aisle=aisle or det.get("aisle", "unknown"),
                            bay=bay if bay is not None else det.get("bay", 0),
                            shelf_level=det.get("shelf_level", 0),
                            product_id=det.get("product_id", "unknown"),
                            confidence=det.get("confidence", 0),
                            consecutive_frames=count,
                        )
                    else:
                        self.alerts_suppressed += 1

        # Reset counters for facings not detected as empty this frame
        for key in list(self.consecutive_tracker[camera_id].keys()):
            if key not in current_empty_keys:
                self.consecutive_tracker[camera_id][key] = 0

    def _make_facing_key(self, aisle: str, bay: int, product_id: str, shelf_level: int) -> str:
        return f"{aisle}:{bay}:{shelf_level}:{product_id}"

    def _can_alert(self, facing_key: str) -> bool:
        """Check if cooldown period has elapsed for this facing."""
        last_alert_time = self.cooldown_tracker.get(facing_key, 0)
        elapsed = time.time() - last_alert_time
        return elapsed >= self.COOLDOWN_SECONDS

    def _publish_alert(self, camera_id: str, facing_key: str, aisle: str,
                       bay: int, shelf_level: int, product_id: str,
                       confidence: float, consecutive_frames: int):
        """Publish OOS alert to MQTT topic."""
        alert_id = str(uuid.uuid4())
        now = datetime.utcnow()

        # Determine priority
        if consecutive_frames >= 10:
            priority = "urgent"
        elif consecutive_frames >= 5:
            priority = "normal"
        else:
            priority = "low"

        alert_payload = {
            "alert_id": alert_id,
            "store_id": self.store_id,
            "aisle": aisle,
            "bay": bay,
            "shelf_level": shelf_level,
            "product_id": product_id,
            "confidence": round(confidence, 4),
            "consecutive_frames": consecutive_frames,
            "timestamp": now.isoformat(),
            "image_url": "",
            "priority": priority,
            "camera_id": camera_id,
        }

        topic = f"stores/{self.store_id}/shelf/oos"

        if self.mqtt_client:
            try:
                result = self.mqtt_client.publish(
                    topic=topic,
                    payload=json.dumps(alert_payload),
                    qos=2,
                    retain=False,
                )
                if result.rc == 0:
                    logger.info(
                        f"OOS Alert published [{alert_id[:8]}]: "
                        f"{aisle}/Bay-{bay}/L{shelf_level} — {product_id} "
                        f"(conf={confidence:.2f}, frames={consecutive_frames})"
                    )
                else:
                    logger.error(f"MQTT publish failed with rc={result.rc}")
            except Exception as e:
                logger.error(f"MQTT publish error: {e}")
        else:
            logger.info(
                f"OOS Alert [NO MQTT] [{alert_id[:8]}]: "
                f"{aisle}/Bay-{bay}/L{shelf_level} — {product_id} "
                f"(conf={confidence:.2f}, frames={consecutive_frames}, priority={priority})"
            )

        # Update cooldown tracker
        self.cooldown_tracker[facing_key] = time.time()
        self.alerts_published += 1

        # Reset consecutive counter after alert
        for cam_trackers in self.consecutive_tracker.values():
            if facing_key in cam_trackers:
                cam_trackers[facing_key] = 0

    def get_stats(self) -> dict:
        """Return publisher statistics."""
        return {
            "alerts_published": self.alerts_published,
            "alerts_suppressed": self.alerts_suppressed,
            "active_trackers": sum(
                len(t) for t in self.consecutive_tracker.values()
            ),
            "active_cooldowns": len(self.cooldown_tracker),
        }


class MQTTTopicSchema:
    """
    MQTT Topic Hierarchy for Smart Store Operations.

    stores/{store_id}/shelf/oos          — Out-of-stock alerts (QoS 2)
    stores/{store_id}/shelf/planogram    — Planogram compliance updates (QoS 1)
    stores/{store_id}/shelf/state        — Fused shelf state (QoS 0)
    stores/{store_id}/queue/status       — Queue depth updates (QoS 0)
    stores/{store_id}/queue/alert        — Queue threshold alerts (QoS 2)
    stores/{store_id}/lp/alert           — Loss prevention alerts (QoS 2)
    stores/{store_id}/lp/behaviour       — Behaviour analytics (QoS 1)
    stores/{store_id}/sensor/weight      — Weight sensor telemetry (QoS 0)
    stores/{store_id}/sensor/rfid        — RFID read events (QoS 0)
    stores/{store_id}/system/health      — Edge node health (QoS 1)
    stores/{store_id}/system/heartbeat   — Heartbeat (QoS 0, retained)
    stores/{store_id}/restock/task       — Restock task creation (QoS 2)
    stores/{store_id}/restock/complete   — Restock task completion (QoS 1)
    """

    TOPICS = {
        "shelf_oos": "stores/{store_id}/shelf/oos",
        "shelf_planogram": "stores/{store_id}/shelf/planogram",
        "shelf_state": "stores/{store_id}/shelf/state",
        "queue_status": "stores/{store_id}/queue/status",
        "queue_alert": "stores/{store_id}/queue/alert",
        "lp_alert": "stores/{store_id}/lp/alert",
        "lp_behaviour": "stores/{store_id}/lp/behaviour",
        "sensor_weight": "stores/{store_id}/sensor/weight",
        "sensor_rfid": "stores/{store_id}/sensor/rfid",
        "system_health": "stores/{store_id}/system/health",
        "system_heartbeat": "stores/{store_id}/system/heartbeat",
        "restock_task": "stores/{store_id}/restock/task",
        "restock_complete": "stores/{store_id}/restock/complete",
    }

    QOS_LEVELS = {
        "shelf_oos": 2,
        "shelf_planogram": 1,
        "shelf_state": 0,
        "queue_status": 0,
        "queue_alert": 2,
        "lp_alert": 2,
        "lp_behaviour": 1,
        "sensor_weight": 0,
        "sensor_rfid": 0,
        "system_health": 1,
        "system_heartbeat": 0,
        "restock_task": 2,
        "restock_complete": 1,
    }

    RETAINED = {"system_heartbeat"}

    @classmethod
    def get_topic(cls, key: str, store_id: str) -> str:
        return cls.TOPICS[key].format(store_id=store_id)

    @classmethod
    def get_qos(cls, key: str) -> int:
        return cls.QOS_LEVELS.get(key, 0)

    @classmethod
    def is_retained(cls, key: str) -> bool:
        return key in cls.RETAINED
