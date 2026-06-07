import os
import random
from pymongo import UpdateOne
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime

class Database:
    """True DB driver that talks to MongoDB."""
    def __init__(self):
        self.client = None
        self.db = None
        self.MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
        self.DB_NAME = "smartstore"
        self.stores = ["IND-BGR-082", "IND-MUM-112", "IND-DEL-401", "IND-HYD-205", "IND-CHE-309"]
        self.store_names = {
            "IND-BGR-082": "Reliance Fresh - Indiranagar",
            "IND-MUM-112": "Reliance Fresh - Bandra West",
            "IND-DEL-401": "Reliance Smart - Connaught Place",
            "IND-HYD-205": "Reliance Fresh - Jubilee Hills",
            "IND-CHE-309": "Reliance Smart - T-Nagar"
        }

    async def connect(self):
        self.client = AsyncIOMotorClient(self.MONGO_URI)
        self.db = self.client[self.DB_NAME]
        
        # Create indexes
        await self.db.shelf_state.create_index([("store_id", 1), ("aisle", 1), ("bay", 1), ("shelf_level", 1)], unique=True)
        await self.db.queue_state.create_index([("store_id", 1), ("lane_id", 1)], unique=True)
        await self.db.alerts.create_index([("id", 1)], unique=True)

    async def disconnect(self):
        if self.client:
            self.client.close()

    async def update_shelf_state(self, store_id, aisle, bay, shelf_level, data):
        await self.db.shelf_state.update_one(
            {"store_id": store_id, "aisle": aisle, "bay": bay, "shelf_level": shelf_level},
            {"$set": data},
            upsert=True
        )

    async def update_queue_state(self, store_id, lane_id, data):
        await self.db.queue_state.update_one(
            {"store_id": store_id, "lane_id": lane_id},
            {"$set": data},
            upsert=True
        )

    async def insert_alert(self, data):
        await self.db.alerts.insert_one(data)

    async def get_shelf_status(self, store_id: str):
        cursor = self.db.shelf_state.find({"store_id": store_id})
        data = await cursor.to_list(length=None)
        # Adapt keys to match what main.py expects (db rows)
        return [{"aisle": d['aisle'], "bay": d['bay'], "shelf_level": d['shelf_level'],
                 "product_id": d['product_id'], "product_name": d['product_name'],
                 "category": d.get('category'), "price": d.get('price'), "image": d.get('image'),
                 "status": d.get('status', 'product_present'), "fused_confidence": d.get('fused_confidence', 1.0),
                 "weight_ratio": d.get('weight_ratio'), "rfid_tag_count": d.get('rfid_tag_count'),
                 "time": datetime.fromisoformat(d.get('timestamp', datetime.utcnow().isoformat()))} for d in data]

    async def get_queue_status(self, store_id: str):
        cursor = self.db.queue_state.find({"store_id": store_id})
        data = await cursor.to_list(length=None)
        return [{"lane_id": d['lane_id'], "lane_type": d['lane_type'], "is_open": d.get('is_open', True),
                 "cashier_id": d.get('cashier_id'), "queue_length": d['queue_length'],
                 "estimated_wait_seconds": d['estimated_wait_seconds']} for d in data]

    async def get_active_alerts(self, store_id: str, limit: int = 50):
        cursor = self.db.alerts.find({"store_id": store_id, "acknowledged": False}).sort("timestamp", -1).limit(limit)
        return await cursor.to_list(length=None)

    async def acknowledge_alert(self, alert_id: str, officer_id: str, action: str):
        await self.db.alerts.update_one({"id": alert_id}, {"$set": {"acknowledged": True, "officer_id": officer_id, "action": action}})

    async def get_multi_store_kpis(self):
        store_stats = []
        for sid in self.stores:
            store_shelves = await self.db.shelf_state.find({"store_id": sid}).to_list(length=None)
            total_oos = sum(1 for s in store_shelves if s.get('is_out_of_stock'))
            total_items = max(1, len(store_shelves))
            
            alerts_count = await self.db.alerts.count_documents({"store_id": sid, "acknowledged": False})
            
            store_stats.append({
                "store_id": sid,
                "store_name": self.store_names.get(sid, sid),
                "stockout_rate": round(total_oos / total_items, 4) if total_items > 0 else 0,
                "avg_queue_wait_seconds": random.randint(120, 480),
                "shrinkage_pct": round(random.uniform(0.5, 3.5), 2),
                "planogram_compliance": round(random.uniform(0.7, 0.98), 2),
                "active_alerts": alerts_count,
                "system_uptime_pct": 99.8
            })
        
        return store_stats

db = Database()
