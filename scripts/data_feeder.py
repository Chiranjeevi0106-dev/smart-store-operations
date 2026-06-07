import json
import time
import random
import paho.mqtt.client as mqtt
from datetime import datetime

# ─── Configuration ────────────────────────────────────────────────────────────
MQTT_HOST = "localhost"
STORE_ID = "STORE-001"

client = mqtt.Client("sensor-feeder")
client.connect(MQTT_HOST, 1883, 60)

def publish_event(topic, data):
    client.publish(topic, json.dumps(data))
    print(f"Published to {topic}: {data.get('type') or data.get('alert_type')}")

def simulate_real_time():
    print("Starting Real-Time Data Feeder...")
    print("This mimics real camera/sensor metadata entering the system.")
    
    aisles = ["A1", "A2", "B1"]
    products = ["PROD-101", "PROD-102", "PROD-201"]

    while True:
        # 1. Random Shelf Update (Camera/Weight/RFID)
        aisle = random.choice(aisles)
        prod = random.choice(products)
        is_oos = random.random() < 0.1
        
        shelf_data = {
            "store_id": STORE_ID,
            "aisle": aisle,
            "bay": random.randint(1, 4),
            "shelf_level": random.randint(0, 2),
            "product_id": prod,
            "sku_code": prod,
            "camera_status": "empty_facing" if is_oos else "product_present",
            "camera_confidence": 0.98,
            "weight_grams": 0 if is_oos else 500,
            "weight_expected_grams": 500,
            "weight_ratio": 0 if is_oos else 1.0,
            "rfid_present": not is_oos,
            "rfid_tag_count": 0 if is_oos else 5,
            "fused_confidence": 0.99,
            "is_out_of_stock": is_oos,
            "timestamp": datetime.utcnow().isoformat()
        }
        # Publish to Kafka (via MQTT bridge if exists, or direct for this script)
        # For simplicity in this script, we'll format it as a fused state and assume the consumer expects it
        publish_event("smartstore.shelf.state", shelf_data)

        # 2. Random Queue Update
        queue_data = {
            "store_id": STORE_ID,
            "lane_id": random.randint(1, 5),
            "lane_type": "manned",
            "is_open": True,
            "queue_length": random.randint(1, 8),
            "estimated_wait_seconds": random.randint(60, 480),
            "timestamp": datetime.utcnow().isoformat()
        }
        publish_event("smartstore.queue.events", queue_data)

        # 3. Occasional Critical LP Alert
        if random.random() < 0.05:
            lp_data = {
                "store_id": STORE_ID,
                "zone": "A1-Dairies",
                "alert_type": "lp_behaviour",
                "behaviour_class": "concealment",
                "confidence": 0.89,
                "severity": "urgent",
                "message": "Potential concealment gesture detected",
                "timestamp": datetime.utcnow().isoformat()
            }
            publish_event("smartstore.lp.alerts", lp_data)

        time.sleep(random.uniform(2, 5))

if __name__ == "__main__":
    simulate_real_time()
