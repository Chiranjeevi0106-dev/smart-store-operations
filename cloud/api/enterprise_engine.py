import asyncio
import json
import uuid
from datetime import datetime
from collections import deque

class EnterpriseEngine:
    """
    Acts as the 'Single Source of Truth' mimicking a 
    production Kafka + TimescaleDB + MQTT stack in-memory.
    """
    def __init__(self):
        self.message_bus = asyncio.Queue()
        self.shelf_state = {}  # (store_id, aisle, bay, level) -> state
        self.queue_state = {}  # (store_id, lane_id) -> state
        self.alerts = deque(maxlen=200)
        self.stores = ["IND-BGR-082", "IND-MUM-112", "IND-DEL-401", "IND-HYD-205", "IND-CHE-309"]
        self.store_names = {
            "IND-BGR-082": "Reliance Fresh - Indiranagar",
            "IND-MUM-112": "Reliance Fresh - Bandra West",
            "IND-DEL-401": "Reliance Smart - Connaught Place",
            "IND-HYD-205": "Reliance Fresh - Jubilee Hills",
            "IND-CHE-309": "Reliance Smart - T-Nagar"
        }
        
        try:
            # Try to load enriched data from external API script first
            import os
            base_path = os.path.dirname(os.path.abspath(__file__))
            fname = os.path.join(base_path, "master_items_enriched.json")
            if not os.path.exists(fname):
                fname = os.path.join(base_path, "master_items.json")
            
            with open(fname, "r") as f:
                self.products = json.load(f)
        except Exception as e:
            print(f"Error loading product data: {e}")
            self.products = [
                {"id": "AMUL-001", "name": "Amul Gold Milk 500ml", "category": "Dairy"},
                {"id": "REL-OIL-05", "name": "Reliance Sunflower Oil 1L", "category": "Staples"}
            ]
        
        self.is_running = False

    async def publish_event(self, topic, data):
        """Simulate Kafka/MQTT publication."""
        event = {"topic": topic, "payload": data, "timestamp": datetime.utcnow().isoformat()}
        await self.message_bus.put(event)
        
        # Internal auto-persistence + MongoDB
        from database import db
        store_id = data.get('store_id', self.stores[0])
        if topic == "smartstore.shelf.state":
            key = (store_id, data['aisle'], data['bay'], data['shelf_level'])
            self.shelf_state[key] = data
            if db.client:
                # Fire and forget or await
                await db.update_shelf_state(store_id, data['aisle'], data['bay'], data['shelf_level'], data)
        elif topic == "smartstore.queue.events":
            key = (store_id, data['lane_id'])
            self.queue_state[key] = data
            if db.client:
                await db.update_queue_state(store_id, data['lane_id'], data)
        elif topic == "smartstore.lp.alerts":
            new_alert = {**data, "id": str(uuid.uuid4()), "acknowledged": False}
            self.alerts.appendleft(new_alert)
            if db.client:
                await db.insert_alert(new_alert)

    async def get_shelf_status(self, store_id):
        return [s for s in self.shelf_state.values() if s['store_id'] == store_id]

    async def get_queue_status(self, store_id):
        return [q for q in self.queue_state.values() if q['store_id'] == store_id]

    async def get_alerts(self, store_id):
        return [a for a in self.alerts if a['store_id'] == store_id]

    async def get_kpis(self):
        store_stats = []
        for sid in self.stores:
            store_shelves = [s for s in self.shelf_state.values() if s['store_id'] == sid]
            total_oos = sum(1 for s in store_shelves if s.get('is_out_of_stock'))
            total_items = max(1, len(store_shelves))
            
            # Simulated metrics for benchmarking
            store_stats.append({
                "store_id": sid,
                "store_name": self.store_names.get(sid, sid),
                "stockout_rate": round(total_oos / total_items, 4),
                "avg_queue_wait_seconds": random.randint(120, 480),
                "shrinkage_pct": round(random.uniform(0.5, 3.5), 2),
                "planogram_compliance": round(random.uniform(0.7, 0.98), 2),
                "active_alerts": len([a for a in self.alerts if a['store_id'] == sid and not a['acknowledged']]),
                "system_uptime_pct": 99.8
            })
        
        return {"stores": store_stats}

    async def run_data_feeder(self):
        """mimics real hardware telemetry flow for Reliance Fresh branches."""
        self.is_running = True
        print(f"Enterprise Engine: Telemetry flow started for {len(self.stores)} Reliance Fresh stores.")
        
        # Initialize state for all stores
        categories = list(set(p.get('category', 'General') for p in self.products))
        physical_aisles = ['A1', 'A2', 'A3', 'B1', 'B2', 'C1']
        cat_to_aisle = {cat: physical_aisles[i % len(physical_aisles)] for i, cat in enumerate(categories)}

        for sid in self.stores:
            for cat in categories:
                aisle = cat_to_aisle[cat]
                # Filter products for this category
                aisle_products = [p for p in self.products if p.get('category') == cat]
                if not aisle_products: aisle_products = self.products
                
                for bay in range(1, 9):
                    for level in range(3):
                        p = random.choice(aisle_products)
                        await self.publish_event("smartstore.shelf.state", {
                            "store_id": sid, "aisle": aisle, "bay": bay, "shelf_level": level,
                            "product_id": p['id'], "product_name": p['name'],
                            "category": p.get('category', 'General'),
                            "price": p.get('price', 0),
                            "image": p.get('image'),
                            "status": "product_present", "fused_confidence": 0.99, "is_out_of_stock": False,
                            "timestamp": datetime.utcnow().isoformat(), "weight_ratio": 1.0, 
                            "actual_weight": 500, "expected_weight": 500, "rfid_tag_count": 5
                        })
            
            # Initial Queue state
            for lane in range(1, 4):
                await self.publish_event("smartstore.queue.events", {
                    "store_id": sid, "lane_id": lane, "lane_type": "manned" if lane < 3 else "self-checkout",
                    "is_open": True, "queue_length": random.randint(0, 5),
                    "estimated_wait_seconds": random.randint(0, 300),
                    "timestamp": datetime.utcnow().isoformat()
                })

        while self.is_running:
            # 1. Store state updates
            sid = random.choice(self.stores)
            
            # Randomly trigger a stockout or a restock
            store_shelves = [k for k in self.shelf_state.keys() if k[0] == sid]
            if store_shelves:
                key = random.choice(store_shelves)
                state = self.shelf_state[key].copy()
                
                # Logic: more likely to go out of stock if not already, or restock if it is OOS
                if state["is_out_of_stock"]:
                    event_type = "restock" if random.random() < 0.3 else "maintain"
                else:
                    event_type = "sale" if random.random() < 0.15 else "maintain"
                
                if event_type == "sale":
                    state["is_out_of_stock"] = True
                    state["status"] = "empty_facing"
                    state["weight_ratio"] = 0.0
                    state["rfid_tag_count"] = 0
                    await self.publish_event("smartstore.shelf.state", state)
                    # Alert for OOS
                    await self.publish_event("smartstore.lp.alerts", {
                        "store_id": sid, "zone": state['aisle'], "alert_type": "shelf_oos",
                        "severity": "normal", "timestamp": datetime.utcnow().isoformat(),
                        "message": f"Out of Stock: {state['product_name']} in Aisle {state['aisle']}"
                    })
                elif event_type == "restock":
                    state["is_out_of_stock"] = False
                    state["status"] = "product_present"
                    state["weight_ratio"] = 1.0
                    state["rfid_tag_count"] = 5
                    await self.publish_event("smartstore.shelf.state", state)

            # 2. Queue movement
            lane_id = random.randint(1, 3)
            q_len = random.randint(0, 15)
            await self.publish_event("smartstore.queue.events", {
                "store_id": sid, "lane_id": lane_id, "lane_type": "manned",
                "is_open": True, "queue_length": q_len,
                "estimated_wait_seconds": q_len * 45,
                "timestamp": datetime.utcnow().isoformat()
            })

            # 3. Security/LP events
            if random.random() < 0.03:
                behaviour = random.choice(["concealment", "loitering", "grazing", "trolley_abandonment"])
                severity = "urgent" if behaviour == "concealment" else "warning"
                await self.publish_event("smartstore.lp.alerts", {
                  "store_id": sid, "zone": random.choice(["Oils", "Cosmetics", "Dairy"]), 
                  "alert_type": "lp_behaviour", 
                  "behaviour_class": behaviour, "confidence": round(random.uniform(0.85, 0.98), 2), 
                  "severity": severity,
                  "timestamp": datetime.utcnow().isoformat(), 
                  "message": f"Security Alert: Predicted {behaviour} detected @ {sid}"
                })

            await asyncio.sleep(random.uniform(0.5, 2.0))

import random # for run_data_feeder
engine = EnterpriseEngine()
