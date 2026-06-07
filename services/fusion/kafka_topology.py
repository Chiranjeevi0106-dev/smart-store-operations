"""
Smart Store Operations — Kafka Streams Sensor Fusion
Phase 5: Sensor Fusion & Replenishment Engine

Joins 3 event streams (camera OOS, shelf weight, RFID reads) on a
30-second tumbling window. Outputs unified ShelfState event per SKU per bay.
"""

import json
import logging
import time
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass, field, asdict
from collections import defaultdict
from enum import Enum

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


# ─── Event Types ──────────────────────────────────────────────────────────────

class EventType(str, Enum):
    CAMERA_OOS = "camera_oos"
    WEIGHT_SENSOR = "weight_sensor"
    RFID_READ = "rfid_read"


@dataclass
class CameraEvent:
    store_id: str
    aisle: str
    bay: int
    shelf_level: int
    product_id: str
    status: str  # "empty_facing", "product_present", etc.
    confidence: float
    camera_id: str
    timestamp: str


@dataclass
class WeightEvent:
    store_id: str
    aisle: str
    bay: int
    shelf_level: int
    product_id: str
    weight_grams: float
    expected_weight_grams: float
    sensor_id: str
    timestamp: str


@dataclass
class RFIDEvent:
    store_id: str
    aisle: str
    bay: int
    product_id: str
    epc_tags: List[str]
    expected_tag_count: int
    reader_id: str
    timestamp: str


@dataclass
class ShelfStateEvent:
    """Unified shelf state output after sensor fusion."""
    event_id: str
    store_id: str
    aisle: str
    bay: int
    shelf_level: int
    product_id: str
    sku_code: str

    # Individual sensor readings
    camera_status: Optional[str] = None
    camera_confidence: Optional[float] = None
    weight_grams: Optional[float] = None
    weight_expected_grams: Optional[float] = None
    weight_ratio: Optional[float] = None
    rfid_present: Optional[bool] = None
    rfid_tag_count: Optional[int] = None
    rfid_expected_count: Optional[int] = None

    # Fused result
    fused_confidence: float = 0.0
    is_out_of_stock: bool = False

    # Metadata
    sensors_reporting: int = 0
    window_start: str = ""
    window_end: str = ""
    timestamp: str = ""


# ─── Bayesian Sensor Fusion ──────────────────────────────────────────────────

class BayesianFusionEngine:
    """
    Bayesian fusion model weighting each sensor source.
    Weights: camera=0.7, weight=0.85, RFID=0.9

    Computes fused probability that a shelf position is out of stock.
    prior P(OOS) = 0.08 (baseline stockout rate)
    """

    SENSOR_WEIGHTS = {
        "camera": 0.70,
        "weight": 0.85,
        "rfid": 0.90,
    }

    # Likelihood ratios: P(sensor_signal | OOS) / P(sensor_signal | in_stock)
    LIKELIHOOD_OOS = {
        "camera": 0.92,    # P(camera detects empty | actually OOS)
        "weight": 0.95,    # P(weight low | actually OOS)
        "rfid": 0.97,      # P(RFID missing | actually OOS)
    }

    LIKELIHOOD_INSTOCK = {
        "camera": 0.08,    # P(camera false positive | actually in stock)
        "weight": 0.05,    # P(weight false positive | actually in stock)
        "rfid": 0.03,      # P(RFID false positive | actually in stock)
    }

    PRIOR_OOS = 0.08  # Baseline stockout rate

    def fuse(
        self,
        camera_signal: Optional[float] = None,
        weight_signal: Optional[float] = None,
        rfid_signal: Optional[float] = None,
    ) -> float:
        """
        Compute fused out-of-stock probability using Bayesian update.

        Each signal is a probability [0, 1] that the sensor indicates OOS.
        Returns fused probability of OOS.
        """
        posterior = self.PRIOR_OOS
        signals = {}

        if camera_signal is not None:
            signals["camera"] = camera_signal
        if weight_signal is not None:
            signals["weight"] = weight_signal
        if rfid_signal is not None:
            signals["rfid"] = rfid_signal

        if not signals:
            return posterior

        for sensor, signal in signals.items():
            weight = self.SENSOR_WEIGHTS[sensor]

            # Weighted likelihood
            p_signal_oos = self.LIKELIHOOD_OOS[sensor] * signal + (1 - self.LIKELIHOOD_OOS[sensor]) * (1 - signal)
            p_signal_instock = self.LIKELIHOOD_INSTOCK[sensor] * signal + (1 - self.LIKELIHOOD_INSTOCK[sensor]) * (1 - signal)

            # Apply sensor weight
            p_signal_oos = weight * p_signal_oos + (1 - weight) * 0.5
            p_signal_instock = weight * p_signal_instock + (1 - weight) * 0.5

            # Bayesian update
            numerator = p_signal_oos * posterior
            denominator = numerator + p_signal_instock * (1 - posterior)

            if denominator > 0:
                posterior = numerator / denominator

        return round(min(max(posterior, 0.0), 1.0), 4)


# ─── Tumbling Window Manager ─────────────────────────────────────────────────

class TumblingWindowManager:
    """
    Manages 30-second tumbling windows for event aggregation.
    Joins events from 3 streams by (store_id, aisle, bay, product_id) key.
    """

    WINDOW_SIZE_SECONDS = 30

    def __init__(self, fusion_engine: BayesianFusionEngine):
        self.fusion = fusion_engine
        # Key -> {camera: [...], weight: [...], rfid: [...]}
        self.current_window: Dict[str, Dict[str, list]] = defaultdict(
            lambda: {"camera": [], "weight": [], "rfid": []}
        )
        self.window_start = datetime.utcnow()
        self.sku_mapping = {}  # product_id -> sku_code

    def _make_key(self, store_id: str, aisle: str, bay: int, product_id: str) -> str:
        return f"{store_id}:{aisle}:{bay}:{product_id}"

    def _parse_key(self, key: str) -> dict:
        parts = key.split(":")
        return {
            "store_id": parts[0],
            "aisle": parts[1],
            "bay": int(parts[2]),
            "product_id": parts[3],
        }

    def add_camera_event(self, event: CameraEvent):
        key = self._make_key(event.store_id, event.aisle, event.bay, event.product_id)
        self.current_window[key]["camera"].append(event)

    def add_weight_event(self, event: WeightEvent):
        key = self._make_key(event.store_id, event.aisle, event.bay, event.product_id)
        self.current_window[key]["weight"].append(event)

    def add_rfid_event(self, event: RFIDEvent):
        key = self._make_key(event.store_id, event.aisle, event.bay, event.product_id)
        self.current_window[key]["rfid"].append(event)

    def flush_window(self) -> List[ShelfStateEvent]:
        """Process current window and emit ShelfState events."""
        window_end = datetime.utcnow()
        results = []

        for key, streams in self.current_window.items():
            key_parts = self._parse_key(key)
            state = self._fuse_streams(key_parts, streams, self.window_start, window_end)
            if state:
                results.append(state)

        # Reset window
        self.current_window = defaultdict(lambda: {"camera": [], "weight": [], "rfid": []})
        self.window_start = window_end

        logger.info(f"Window flushed: {len(results)} ShelfState events emitted")
        return results

    def _fuse_streams(
        self, key_parts: dict, streams: dict,
        window_start: datetime, window_end: datetime,
    ) -> Optional[ShelfStateEvent]:
        """Fuse sensor streams for one SKU-bay combination."""

        camera_events = streams["camera"]
        weight_events = streams["weight"]
        rfid_events = streams["rfid"]

        sensors_reporting = sum(1 for s in [camera_events, weight_events, rfid_events] if s)

        if sensors_reporting == 0:
            return None

        # Aggregate camera signals
        camera_signal = None
        camera_status = None
        camera_conf = None
        if camera_events:
            empty_confs = [e.confidence for e in camera_events if e.status == "empty_facing"]
            if empty_confs:
                camera_signal = max(empty_confs)
                camera_status = "empty_facing"
                camera_conf = camera_signal
            else:
                camera_signal = 0.0
                camera_status = camera_events[-1].status
                camera_conf = camera_events[-1].confidence

        # Aggregate weight signals
        weight_signal = None
        weight_grams = None
        weight_expected = None
        weight_ratio = None
        if weight_events:
            latest_weight = weight_events[-1]
            weight_grams = latest_weight.weight_grams
            weight_expected = latest_weight.expected_weight_grams
            if weight_expected > 0:
                weight_ratio = weight_grams / weight_expected
                weight_signal = max(0, 1.0 - weight_ratio)
            else:
                weight_signal = 0.0

        # Aggregate RFID signals
        rfid_signal = None
        rfid_present = None
        rfid_count = None
        rfid_expected = None
        if rfid_events:
            latest_rfid = rfid_events[-1]
            rfid_count = len(latest_rfid.epc_tags)
            rfid_expected = latest_rfid.expected_tag_count
            rfid_present = rfid_count > 0
            if rfid_expected > 0:
                rfid_signal = max(0, 1.0 - rfid_count / rfid_expected)
            else:
                rfid_signal = 0.0

        # Bayesian fusion
        fused_confidence = self.fusion.fuse(
            camera_signal=camera_signal,
            weight_signal=weight_signal,
            rfid_signal=rfid_signal,
        )

        shelf_level = 0
        if camera_events:
            shelf_level = camera_events[0].shelf_level
        elif weight_events:
            shelf_level = weight_events[0].shelf_level

        return ShelfStateEvent(
            event_id=str(uuid.uuid4()),
            store_id=key_parts["store_id"],
            aisle=key_parts["aisle"],
            bay=key_parts["bay"],
            shelf_level=shelf_level,
            product_id=key_parts["product_id"],
            sku_code=self.sku_mapping.get(key_parts["product_id"], key_parts["product_id"]),
            camera_status=camera_status,
            camera_confidence=camera_conf,
            weight_grams=weight_grams,
            weight_expected_grams=weight_expected,
            weight_ratio=weight_ratio,
            rfid_present=rfid_present,
            rfid_tag_count=rfid_count,
            rfid_expected_count=rfid_expected,
            fused_confidence=fused_confidence,
            is_out_of_stock=fused_confidence >= 0.65,
            sensors_reporting=sensors_reporting,
            window_start=window_start.isoformat(),
            window_end=window_end.isoformat(),
            timestamp=datetime.utcnow().isoformat(),
        )


# ─── Kafka Consumer/Producer (production topology) ───────────────────────────

class KafkaStreamTopology:
    """
    Kafka Streams-like topology for Python.

    Input Topics:
      - smartstore.camera.oos     (camera OOS detections)
      - smartstore.sensor.weight  (shelf weight readings)
      - smartstore.sensor.rfid    (RFID read events)

    Output Topic:
      - smartstore.shelf.state    (fused ShelfState events)

    Join: 30-second tumbling window on key (store_id, aisle, bay, product_id)
    """

    INPUT_TOPICS = [
        "smartstore.camera.oos",
        "smartstore.sensor.weight",
        "smartstore.sensor.rfid",
    ]
    OUTPUT_TOPIC = "smartstore.shelf.state"

    def __init__(self, kafka_bootstrap: str = "localhost:9092", group_id: str = "sensor-fusion"):
        self.kafka_bootstrap = kafka_bootstrap
        self.group_id = group_id
        self.fusion_engine = BayesianFusionEngine()
        self.window_manager = TumblingWindowManager(self.fusion_engine)
        self.producer = None
        self.consumer = None

    def start(self):
        """Start the Kafka stream processing loop."""
        try:
            from confluent_kafka import Consumer, Producer
        except ImportError:
            logger.error("confluent-kafka not installed. Run: pip install confluent-kafka")
            logger.info("Starting in simulation mode...")
            self._run_simulation()
            return

        self.consumer = Consumer({
            "bootstrap.servers": self.kafka_bootstrap,
            "group.id": self.group_id,
            "auto.offset.reset": "latest",
            "enable.auto.commit": True,
            "session.timeout.ms": 30000,
        })

        self.producer = Producer({
            "bootstrap.servers": self.kafka_bootstrap,
            "acks": "all",
            "compression.type": "snappy",
        })

        self.consumer.subscribe(self.INPUT_TOPICS)
        logger.info(f"Subscribed to topics: {self.INPUT_TOPICS}")

        window_interval = TumblingWindowManager.WINDOW_SIZE_SECONDS
        last_flush = time.time()

        try:
            while True:
                msg = self.consumer.poll(timeout=1.0)

                if msg is not None and not msg.error():
                    self._process_message(msg.topic(), json.loads(msg.value()))

                # Flush window periodically
                if time.time() - last_flush >= window_interval:
                    fused_states = self.window_manager.flush_window()
                    for state in fused_states:
                        self._emit_shelf_state(state)
                    last_flush = time.time()

        except KeyboardInterrupt:
            logger.info("Shutting down...")
        finally:
            self.consumer.close()

    def _process_message(self, topic: str, data: dict):
        """Route message to appropriate window stream."""
        if topic == "smartstore.camera.oos":
            event = CameraEvent(**data)
            self.window_manager.add_camera_event(event)
        elif topic == "smartstore.sensor.weight":
            event = WeightEvent(**data)
            self.window_manager.add_weight_event(event)
        elif topic == "smartstore.sensor.rfid":
            event = RFIDEvent(**data)
            self.window_manager.add_rfid_event(event)

    def _emit_shelf_state(self, state: ShelfStateEvent):
        """Publish fused ShelfState to output topic."""
        payload = json.dumps(asdict(state))

        if self.producer:
            self.producer.produce(
                self.OUTPUT_TOPIC,
                key=f"{state.store_id}:{state.aisle}:{state.bay}:{state.product_id}",
                value=payload,
            )
            self.producer.flush()
        else:
            logger.info(f"ShelfState: {state.aisle}/Bay-{state.bay} "
                        f"product={state.product_id} fused={state.fused_confidence:.3f} "
                        f"oos={state.is_out_of_stock}")

    def _run_simulation(self):
        """Run fusion in simulation mode with mock events."""
        import random

        logger.info("Running sensor fusion simulation...")
        window_interval = TumblingWindowManager.WINDOW_SIZE_SECONDS

        products = [f"PROD-{i:03d}" for i in range(1, 21)]
        aisles = ["A1", "A2", "A3", "B1", "B2"]
        stores = ["STORE-001"]

        for cycle in range(10):
            logger.info(f"\n--- Window Cycle {cycle + 1} ---")

            for _ in range(random.randint(20, 50)):
                product = random.choice(products)
                aisle = random.choice(aisles)
                bay = random.randint(1, 8)
                store = random.choice(stores)

                is_oos = random.random() < 0.12  # 12% chance

                # Camera event
                self.window_manager.add_camera_event(CameraEvent(
                    store_id=store, aisle=aisle, bay=bay, shelf_level=random.randint(0, 3),
                    product_id=product,
                    status="empty_facing" if is_oos else "product_present",
                    confidence=random.uniform(0.85, 0.99) if is_oos else random.uniform(0.7, 0.95),
                    camera_id=f"CAM-{aisle}", timestamp=datetime.utcnow().isoformat(),
                ))

                # Weight event
                expected_weight = random.uniform(200, 5000)
                actual_weight = expected_weight * (random.uniform(0.0, 0.15) if is_oos else random.uniform(0.5, 1.0))
                self.window_manager.add_weight_event(WeightEvent(
                    store_id=store, aisle=aisle, bay=bay, shelf_level=random.randint(0, 3),
                    product_id=product,
                    weight_grams=actual_weight, expected_weight_grams=expected_weight,
                    sensor_id=f"WS-{aisle}-{bay}", timestamp=datetime.utcnow().isoformat(),
                ))

                # RFID event
                expected_tags = random.randint(3, 15)
                actual_tags = random.randint(0, 1) if is_oos else random.randint(max(1, expected_tags - 2), expected_tags)
                self.window_manager.add_rfid_event(RFIDEvent(
                    store_id=store, aisle=aisle, bay=bay, product_id=product,
                    epc_tags=[f"EPC-{uuid.uuid4().hex[:8]}" for _ in range(actual_tags)],
                    expected_tag_count=expected_tags,
                    reader_id=f"RFID-{aisle}", timestamp=datetime.utcnow().isoformat(),
                ))

            # Flush window
            results = self.window_manager.flush_window()
            oos_count = sum(1 for r in results if r.is_out_of_stock)
            logger.info(f"Cycle {cycle + 1}: {len(results)} shelf states, {oos_count} OOS detected")

            for r in results:
                if r.is_out_of_stock:
                    logger.info(
                        f"  ⚠ OOS: {r.aisle}/Bay-{r.bay} {r.product_id} "
                        f"fused={r.fused_confidence:.3f} sensors={r.sensors_reporting}"
                    )

            time.sleep(1)


if __name__ == "__main__":
    topology = KafkaStreamTopology()
    topology.start()
