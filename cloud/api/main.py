import asyncio
import json
import logging
import os
import uuid
from datetime import datetime
from typing import List, Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Depends, WebSocket, WebSocketDisconnect, Query, Path
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
from enum import Enum

from database import db
from enterprise_engine import engine

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# ─── Schemas (Same as before) ──────────────────────────────────────────────────
class FacingStatus(str, Enum):
    PRODUCT_PRESENT = "product_present"
    EMPTY_FACING = "empty_facing"
    WRONG_PRODUCT = "wrong_product"
    PARTIAL_FACING = "partial_facing"

class ShelfItem(BaseModel):
    aisle: str
    bay: int
    shelf_level: int
    product_id: str
    product_name: str
    category: Optional[str] = None
    price: Optional[float] = None
    image: Optional[str] = None
    status: FacingStatus
    fused_confidence: float
    weight_ratio: Optional[float] = None
    rfid_tag_count: Optional[int] = None
    last_updated: datetime

class ShelfStatusResponse(BaseModel):
    store_id: str
    timestamp: datetime
    items: List[ShelfItem]

class LaneStatus(BaseModel):
    lane_id: int
    lane_type: str
    is_open: bool
    cashier_id: Optional[str] = None
    queue_length: int
    estimated_wait_seconds: float

class QueueStatusResponse(BaseModel):
    store_id: str
    timestamp: datetime
    lanes: List[LaneStatus]

class StoreKPI(BaseModel):
    store_id: str
    store_name: str
    stockout_rate: float
    avg_queue_wait_seconds: float
    shrinkage_pct: float
    planogram_compliance: float
    active_alerts: int
    system_uptime_pct: float

class MultiStoreKPIResponse(BaseModel):
    stores: List[StoreKPI]

# ─── WebSocket Manager ────────────────────────────────────────────────────────
class ConnectionManager:
    def __init__(self):
        self.active_connections: dict = {}

    async def connect(self, websocket: WebSocket, store_id: str):
        await websocket.accept()
        if store_id not in self.active_connections:
            self.active_connections[store_id] = []
        self.active_connections[store_id].append(websocket)

    def disconnect(self, websocket: WebSocket, store_id: str):
        if store_id in self.active_connections:
            self.active_connections[store_id] = [
                ws for ws in self.active_connections[store_id] if ws != websocket
            ]

    async def broadcast(self, store_id: str, message: dict):
        if store_id in self.active_connections:
            for ws in self.active_connections[store_id]:
                try:
                    await ws.send_json(message)
                except:
                    pass

ws_manager = ConnectionManager()

# ─── Enterprise Bus Worker (Mimics Kafka Consumer) ───────────────────────────
async def bus_worker():
    print("Standalone Enterprise Worker: Listening to internal message bus...")
    while True:
        event = await engine.message_bus.get()
        topic = event['topic']
        data = event['payload']
        store_id = data.get('store_id', 'STORE-001')

        msg_type = "alert"
        if "shelf" in topic: msg_type = "shelf_update"
        elif "queue" in topic: msg_type = "queue_update"

        await ws_manager.broadcast(store_id, {
            "type": msg_type,
            "data": data
        })

# ─── App Lifecycle ────────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Connect to MongoDB
    await db.connect()
    # Start the data feeder (mimics actual hardware)
    feeder_task = asyncio.create_task(engine.run_data_feeder())
    # Start the bus worker (mimics cloud-side consumer)
    worker_task = asyncio.create_task(bus_worker())
    yield
    feeder_task.cancel()
    worker_task.cancel()
    await db.disconnect()

app = FastAPI(title="Smart Store Enterprise-Live API", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# ─── REST Endpoints (Now fetching from Engine via Database class) ──────────────
@app.get("/stores/{store_id}/shelf-status", response_model=ShelfStatusResponse)
async def get_shelf_status(store_id: str):
    rows = await db.get_shelf_status(store_id)
    items = [ShelfItem(**r, last_updated=r['time']) for r in rows]
    return ShelfStatusResponse(store_id=store_id, timestamp=datetime.utcnow(), items=items)

@app.get("/stores/{store_id}/queue-status", response_model=QueueStatusResponse)
async def get_queue_status(store_id: str):
    rows = await db.get_queue_status(store_id)
    lanes = [LaneStatus(**r) for r in rows]
    return QueueStatusResponse(store_id=store_id, timestamp=datetime.utcnow(), lanes=lanes)

@app.get("/reports/multi-store-kpis", response_model=MultiStoreKPIResponse)
async def get_multi_store_kpis():
    rows = await db.get_multi_store_kpis()
    stores = [StoreKPI(**r) for r in rows]
    return MultiStoreKPIResponse(stores=stores)

@app.websocket("/ws/alerts/{store_id}")
async def websocket_alerts(websocket: WebSocket, store_id: str):
    await ws_manager.connect(websocket, store_id)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket, store_id)

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
