import asyncio
import json
import logging
import os
import asyncpg
from aiokafka import AIOKafkaConsumer
from datetime import datetime

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://smartstore:smartstore_dev@localhost:5432/smartstore")
KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")

TOPICS = [
    "smartstore.shelf.state",
    "smartstore.queue.events",
    "smartstore.lp.alerts"
]

class DBConsumer:
    def __init__(self):
        self.pool = None

    async def connect_db(self):
        self.pool = await asyncpg.create_pool(DATABASE_URL)
        logger.info("Connected to TimescaleDB")

    async def write_shelf_state(self, data):
        query = """
            INSERT INTO shelf_state (
                time, store_id, aisle, bay, shelf_level, product_id, sku_code,
                camera_status, camera_confidence, weight_grams, weight_expected_grams,
                weight_ratio, rfid_present, rfid_tag_count, fused_confidence, is_out_of_stock
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16)
        """
        async with self.pool.acquire() as conn:
            await conn.execute(query, 
                datetime.fromisoformat(data['timestamp'].replace('Z', '+00:00')),
                data['store_id'], data['aisle'], data['bay'], data['shelf_level'],
                data['product_id'], data['sku_code'], data['camera_status'],
                data['camera_confidence'], data['weight_grams'], data['weight_expected_grams'],
                data['weight_ratio'], data['rfid_present'], data['rfid_tag_count'],
                data['fused_confidence'], data['is_out_of_stock']
            )

    async def write_queue_event(self, data):
        query = """
            INSERT INTO queue_events (
                time, store_id, lane_id, lane_type, is_open, cashier_id,
                queue_length, estimated_wait_seconds
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
        """
        async with self.pool.acquire() as conn:
            await conn.execute(query,
                datetime.fromisoformat(data['timestamp'].replace('Z', '+00:00')),
                data['store_id'], data['lane_id'], data['lane_type'], data['is_open'],
                data.get('cashier_id'), data['queue_length'], data['estimated_wait_seconds']
            )

    async def write_lp_alert(self, data):
        query = """
            INSERT INTO lp_alerts (
                time, store_id, zone, alert_type, behaviour_class, confidence, severity, message
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
        """
        async with self.pool.acquire() as conn:
            await conn.execute(query,
                datetime.fromisoformat(data['timestamp'].replace('Z', '+00:00')),
                data['store_id'], data['zone'], data['alert_type'],
                data.get('behaviour_class'), data['confidence'], data['severity'],
                data.get('message', '')
            )

    async def run(self):
        await self.connect_db()
        consumer = AIOKafkaConsumer(
            *TOPICS,
            bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
            group_id="db-persistence-worker"
        )
        await consumer.start()
        logger.info(f"Subscribed to topics: {TOPICS}")
        try:
            async for msg in consumer:
                try:
                    data = json.loads(msg.value)
                    if msg.topic == "smartstore.shelf.state":
                        await self.write_shelf_state(data)
                    elif msg.topic == "smartstore.queue.events":
                        await self.write_queue_event(data)
                    elif msg.topic == "smartstore.lp.alerts":
                        await self.write_lp_alert(data)
                except Exception as e:
                    logger.error(f"Error persisting to DB: {e}")
        finally:
            await consumer.stop()
            await self.pool.close()

if __name__ == "__main__":
    asyncio.run(DBConsumer().run())
