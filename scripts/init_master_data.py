import asyncio
import asyncpg
import os
import uuid
from datetime import datetime

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://smartstore:smartstore_dev@localhost:5432/smartstore")

async def init_data():
    conn = await asyncpg.connect(DATABASE_URL)
    print("Initializing master data in TimescaleDB...")

    # Insert initial shelf positions for STORE-001
    aisles = ["A1", "A2", "A3", "B1", "B2"]
    products = [
        ("PROD-101", "Full Cream Milk 1L", "Milk"),
        ("PROD-102", "Greek Yogurt 500g", "Dairy"),
        ("PROD-201", "Organic Brown Bread", "Bakery"),
        ("PROD-301", "Dark Chocolate 100g", "Confectionery"),
    ]

    for aisle in aisles:
        for bay in range(1, 4):
            for level in range(3):
                product_id, name, cat = products[(bay + level) % len(products)]
                await conn.execute("""
                    INSERT INTO shelf_state (
                        time, store_id, aisle, bay, shelf_level, product_id, sku_code,
                        camera_status, camera_confidence, fused_confidence, is_out_of_stock, product_name
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
                    ON CONFLICT DO NOTHING
                """, datetime.utcnow(), "STORE-001", aisle, bay, level, product_id, product_id,
                "product_present", 0.95, 0.95, False, name)

    # Insert initial queue state
    for lane in range(1, 6):
        await conn.execute("""
            INSERT INTO queue_events (
                time, store_id, lane_id, lane_type, is_open, queue_length, estimated_wait_seconds
            ) VALUES ($1, $2, $3, $4, $5, $6, $7)
            ON CONFLICT DO NOTHING
        """, datetime.utcnow(), "STORE-001", lane, "self_checkout" if lane > 4 else "manned",
        True, 0, 0)

    print("Master data seeded.")
    await conn.close()

if __name__ == "__main__":
    asyncio.run(init_data())
