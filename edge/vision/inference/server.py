"""
Smart Store Operations — FastAPI Inference Server
Phase 4: Computer Vision Pipeline (Shelf AI)

Serves YOLOv9 shelf detection and ResNet-50 Siamese planogram compliance.
Endpoints: /detect, /planogram, /health
Target: <= 80ms inference on Jetson Orin NX
"""

import asyncio
import base64
import io
import json
import logging
import os
import time
import uuid
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Optional

import numpy as np
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from schemas import (
    DetectionRequest,
    DetectionResponse,
    Detection,
    BoundingBox,
    FacingStatus,
    PlanogramRequest,
    PlanogramResponse,
    FacingDeviation,
    HealthResponse,
    ErrorResponse,
    ShelfOOSAlert,
    AlertPriority,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# ─── Configuration ────────────────────────────────────────────────────────────

YOLO_MODEL_PATH = os.getenv("YOLO_MODEL_PATH", "./models/shelf_yolov9m.engine")
PLANOGRAM_MODEL_PATH = os.getenv("PLANOGRAM_MODEL_PATH", "./models/planogram_siamese.engine")
MQTT_BROKER = os.getenv("MQTT_BROKER", "localhost")
MQTT_PORT = int(os.getenv("MQTT_PORT", "1883"))
CONFIDENCE_THRESHOLD = float(os.getenv("CONFIDENCE_THRESHOLD", "0.5"))
OOS_ALERT_THRESHOLD = float(os.getenv("OOS_ALERT_THRESHOLD", "0.85"))
OOS_CONSECUTIVE_FRAMES = int(os.getenv("OOS_CONSECUTIVE_FRAMES", "3"))
MODEL_VERSION = os.getenv("MODEL_VERSION", "1.0.0")

# ─── Global State ─────────────────────────────────────────────────────────────

class InferenceState:
    """Manages loaded models and inference tracking."""

    def __init__(self):
        self.yolo_model = None
        self.planogram_model = None
        self.start_time = time.time()
        self.inference_count = 0
        self.total_inference_ms = 0.0
        self.oos_tracker = {}  # camera_id -> {product_id -> consecutive_count}
        self.mqtt_client = None

    @property
    def uptime_seconds(self):
        return time.time() - self.start_time

    @property
    def avg_inference_ms(self):
        if self.inference_count == 0:
            return 0.0
        return self.total_inference_ms / self.inference_count

    def track_inference(self, duration_ms: float):
        self.inference_count += 1
        self.total_inference_ms += duration_ms


state = InferenceState()


# ─── Model Loading ────────────────────────────────────────────────────────────

def load_yolo_model(model_path: str):
    """Load YOLOv9 model — supports both PyTorch and TensorRT."""
    try:
        from ultralytics import YOLO
        model = YOLO(model_path)
        logger.info(f"Loaded YOLOv9 model from {model_path}")
        return model
    except ImportError:
        logger.warning("ultralytics not available — running in mock mode")
        return None
    except Exception as e:
        logger.error(f"Failed to load YOLO model: {e}")
        return None


def load_planogram_model(model_path: str):
    """Load Siamese ResNet-50 planogram model."""
    try:
        import torch
        if os.path.exists(model_path):
            model = torch.jit.load(model_path)
            model.eval()
            logger.info(f"Loaded planogram model from {model_path}")
            return model
    except ImportError:
        logger.warning("PyTorch not available — planogram in mock mode")
    except Exception as e:
        logger.error(f"Failed to load planogram model: {e}")
    return None


def setup_mqtt():
    """Initialize MQTT client for alert publishing."""
    try:
        import paho.mqtt.client as mqtt
        client = mqtt.Client(client_id="shelf_ai_server", protocol=mqtt.MQTTv5)
        client.tls_set()
        client.connect(MQTT_BROKER, MQTT_PORT, keepalive=60)
        client.loop_start()
        logger.info(f"MQTT connected to {MQTT_BROKER}:{MQTT_PORT}")
        return client
    except Exception as e:
        logger.warning(f"MQTT connection failed: {e} — alerts will be logged only")
        return None


# ─── Lifespan ─────────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load models on startup, cleanup on shutdown."""
    logger.info("Loading inference models...")
    state.yolo_model = load_yolo_model(YOLO_MODEL_PATH)
    state.planogram_model = load_planogram_model(PLANOGRAM_MODEL_PATH)
    state.mqtt_client = setup_mqtt()
    logger.info("Inference server ready.")
    yield
    logger.info("Shutting down inference server...")
    if state.mqtt_client:
        state.mqtt_client.loop_stop()
        state.mqtt_client.disconnect()


# ─── FastAPI App ──────────────────────────────────────────────────────────────

app = FastAPI(
    title="Smart Store Shelf AI",
    description="YOLOv9 shelf detection and planogram compliance inference API",
    version=MODEL_VERSION,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─── Helpers ──────────────────────────────────────────────────────────────────

def decode_image(image_base64: str) -> np.ndarray:
    """Decode base64 image to numpy array."""
    try:
        from PIL import Image
        img_bytes = base64.b64decode(image_base64)
        img = Image.open(io.BytesIO(img_bytes)).convert("RGB")
        return np.array(img)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid image data: {e}")


def run_yolo_inference(image: np.ndarray) -> list:
    """Run YOLOv9 inference on image."""
    if state.yolo_model is None:
        return _mock_detections()

    results = state.yolo_model(image, conf=CONFIDENCE_THRESHOLD, verbose=False)

    detections = []
    for r in results:
        for box in r.boxes:
            cls_id = int(box.cls[0])
            cls_name = list(FacingStatus)[cls_id].value if cls_id < 4 else "product_present"
            coords = box.xyxyn[0].tolist()
            detections.append(
                Detection(
                    class_name=FacingStatus(cls_name),
                    confidence=float(box.conf[0]),
                    bbox=BoundingBox(
                        x_min=coords[0], y_min=coords[1],
                        x_max=coords[2], y_max=coords[3],
                    ),
                )
            )
    return detections


def _mock_detections() -> list:
    """Generate mock detections for testing without models."""
    import random
    n = random.randint(8, 20)
    statuses = list(FacingStatus)
    detections = []
    for i in range(n):
        status = random.choices(
            statuses,
            weights=[0.65, 0.15, 0.10, 0.10],
            k=1,
        )[0]
        x = (i % 5) * 0.2
        y = (i // 5) * 0.25
        detections.append(
            Detection(
                class_name=status,
                confidence=round(random.uniform(0.7, 0.99), 3),
                bbox=BoundingBox(
                    x_min=round(x, 3),
                    y_min=round(y, 3),
                    x_max=round(min(x + 0.18, 1.0), 3),
                    y_max=round(min(y + 0.23, 1.0), 3),
                ),
            )
        )
    return detections


def _mock_planogram_check(num_facings: int = 12) -> tuple:
    """Generate mock planogram compliance for testing."""
    import random
    deviations = []
    compliant = 0
    for i in range(num_facings):
        is_compliant = random.random() > 0.15
        if is_compliant:
            compliant += 1
        deviations.append(
            FacingDeviation(
                position=i,
                shelf_level=i // 4,
                expected_product_id=f"SKU-{1000 + i}",
                detected_product_id=f"SKU-{1000 + i}" if is_compliant else f"SKU-{2000 + i}",
                status=FacingStatus.PRODUCT_PRESENT if is_compliant else FacingStatus.WRONG_PRODUCT,
                similarity_score=round(random.uniform(0.85, 0.99) if is_compliant else random.uniform(0.2, 0.6), 3),
            )
        )
    score = compliant / num_facings if num_facings > 0 else 0.0
    return score, deviations


def check_oos_alert(camera_id: str, detections: list, store_id: str):
    """Check for consecutive empty facing detections and publish alert."""
    if camera_id not in state.oos_tracker:
        state.oos_tracker[camera_id] = {}

    tracker = state.oos_tracker[camera_id]

    for det in detections:
        if det.class_name == FacingStatus.EMPTY_FACING and det.confidence >= OOS_ALERT_THRESHOLD:
            key = f"{det.aisle or 'unknown'}_{det.bay or 0}_{det.product_id or 'unknown'}"
            tracker[key] = tracker.get(key, 0) + 1

            if tracker[key] >= OOS_CONSECUTIVE_FRAMES:
                alert = ShelfOOSAlert(
                    alert_id=str(uuid.uuid4()),
                    store_id=store_id,
                    aisle=det.aisle or "unknown",
                    bay=det.bay or 0,
                    shelf_level=det.shelf_level or 0,
                    product_id=det.product_id or "unknown",
                    confidence=det.confidence,
                    consecutive_frames=tracker[key],
                    timestamp=datetime.utcnow(),
                    image_url="",
                    priority=AlertPriority.URGENT if tracker[key] >= 5 else AlertPriority.NORMAL,
                    camera_id=camera_id,
                )
                publish_oos_alert(alert)
                tracker[key] = 0
        else:
            for key in list(tracker.keys()):
                tracker[key] = 0


def publish_oos_alert(alert: ShelfOOSAlert):
    """Publish OOS alert to MQTT broker."""
    topic = f"stores/{alert.store_id}/shelf/oos"
    payload = alert.model_dump_json()

    if state.mqtt_client:
        state.mqtt_client.publish(topic, payload, qos=2, retain=False)
        logger.info(f"OOS alert published: {topic} — {alert.product_id}")
    else:
        logger.info(f"OOS alert (no MQTT): {topic} — {alert.product_id} conf={alert.confidence:.2f}")


# ─── Endpoints ────────────────────────────────────────────────────────────────

@app.post("/detect", response_model=DetectionResponse)
async def detect_shelf(request: DetectionRequest):
    """
    Detect shelf product facings in an image.

    Returns bounding boxes with classification:
    product_present, empty_facing, wrong_product, partial_facing
    """
    request_id = str(uuid.uuid4())
    start = time.perf_counter()

    image = decode_image(request.image_base64)
    detections = run_yolo_inference(image)

    inference_ms = (time.perf_counter() - start) * 1000
    state.track_inference(inference_ms)

    for det in detections:
        det.aisle = request.aisle
        det.bay = request.bay

    empty_count = sum(1 for d in detections if d.class_name == FacingStatus.EMPTY_FACING)
    total = len(detections)

    asyncio.create_task(asyncio.to_thread(
        check_oos_alert, request.camera_id, detections, request.store_id
    ))

    return DetectionResponse(
        request_id=request_id,
        store_id=request.store_id,
        camera_id=request.camera_id,
        timestamp=request.timestamp,
        inference_time_ms=round(inference_ms, 2),
        detections=detections,
        total_facings=total,
        empty_facings=empty_count,
        stockout_rate=round(empty_count / total, 4) if total > 0 else 0.0,
        model_version=MODEL_VERSION,
    )


@app.post("/planogram", response_model=PlanogramResponse)
async def check_planogram(request: PlanogramRequest):
    """
    Compare live shelf image against golden planogram.

    Returns compliance score (0-1) and per-facing deviation map.
    """
    request_id = str(uuid.uuid4())
    start = time.perf_counter()

    image = decode_image(request.image_base64)

    if state.planogram_model is not None:
        import torch
        from torchvision import transforms
        transform = transforms.Compose([
            transforms.ToPILImage(),
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        ])
        img_tensor = transform(image).unsqueeze(0)

        with torch.no_grad():
            score = state.planogram_model(img_tensor).item()
            score = max(0.0, min(1.0, score))
        deviations = []
    else:
        score, deviations = _mock_planogram_check()

    inference_ms = (time.perf_counter() - start) * 1000
    state.track_inference(inference_ms)

    compliant = sum(1 for d in deviations if d.status == FacingStatus.PRODUCT_PRESENT)

    return PlanogramResponse(
        request_id=request_id,
        store_id=request.store_id,
        aisle=request.aisle,
        bay=request.bay,
        planogram_id=request.planogram_id,
        timestamp=request.timestamp,
        inference_time_ms=round(inference_ms, 2),
        compliance_score=round(score, 4),
        total_facings=len(deviations),
        compliant_facings=compliant,
        deviations=deviations,
        model_version=MODEL_VERSION,
    )


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """System health check with inference statistics."""
    return HealthResponse(
        status="healthy",
        version=MODEL_VERSION,
        model_version=MODEL_VERSION,
        uptime_seconds=round(state.uptime_seconds, 1),
        inference_count=state.inference_count,
        avg_inference_ms=round(state.avg_inference_ms, 2),
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error="internal_server_error",
            detail=str(exc),
        ).model_dump(),
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "server:app",
        host="0.0.0.0",
        port=8001,
        reload=False,
        workers=1,
        log_level="info",
    )
