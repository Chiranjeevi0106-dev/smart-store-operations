import cv2
import torch
import numpy as np
import time
import json
import paho.mqtt.client as mqtt
import os
from datetime import datetime

# ─── Configuration ────────────────────────────────────────────────────────────
MODEL_PATH = os.getenv("MODEL_PATH", "models/shelf_yolov9m.pt")
MQTT_HOST = os.getenv("MQTT_HOST", "localhost")
STORE_ID = os.getenv("STORE_ID", "STORE-001")
CAMERA_ID = os.getenv("CAMERA_ID", "CAM-01")
AISLE = "A1"
BAY = 1

# MQTT Setup
client = mqtt.Client(f"edge-{CAMERA_ID}")
client.connect(MQTT_HOST, 1883, 60)

def load_model():
    """Load real YOLOv9 model using PyTorch/TensorRT."""
    logger.info(f"Loading model from {MODEL_PATH}...")
    try:
        # In a real environment, we'd use TensorRT for Jetson performance
        # Here we use the standard PyTorch loading
        model = torch.hub.load('WongKinYiu/yolov9', 'custom', path=MODEL_PATH)
        return model
    except Exception as e:
        logger.error(f"Failed to load model: {e}")
        return None

def process_frame(frame, model):
    """Run actual inference on a frame."""
    results = model(frame)
    # Filter for products (assuming class 0 is generic product)
    detections = results.pandas().xyxy[0] 
    return detections

def run_pipeline(source=0):
    """
    Real-time vision pipeline.
    Connects to RTSP/USB camera, runs YOLO, and publishes metadata.
    """
    model = load_model()
    cap = cv2.VideoCapture(source)
    
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret: break
        
        # Inference
        detections = process_frame(frame, model)
        
        # Logic: Compare detections against Planogram
        # For simplicity, we detect "empty space" class if model trained for it
        # or calculate density
        
        # Map detections to shelf positions (simplified)
        for _, det in detections.iterrows():
            payload = {
                "store_id": STORE_ID,
                "camera_id": CAMERA_ID,
                "aisle": AISLE,
                "bay": BAY,
                "shelf_level": 1,
                "product_id": "PROD-101",
                "status": "product_present" if det['confidence'] > 0.5 else "empty_facing",
                "confidence": float(det['confidence']),
                "timestamp": datetime.utcnow().isoformat()
            }
            client.publish(f"smartstore/camera/oos/{STORE_ID}", json.dumps(payload))
        
        # Limit processing rate for demo if needed
        time.sleep(0.1)

    cap.release()

if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("VisionEdge")
    
    # Run pipeline on a sample video file if source 0 isn't available
    run_pipeline(source="sample_store_aisle.mp4")
