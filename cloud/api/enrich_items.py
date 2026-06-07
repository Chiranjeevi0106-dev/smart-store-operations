import requests
import json
import time
import os

def enrich_data():
    print("Enriching Master Data with Open Food Facts Search API...")
    base_path = os.path.dirname(os.path.abspath(__file__))
    input_file = os.path.join(base_path, "master_items.json")
    output_file = os.path.join(base_path, "master_items_enriched.json")
    
    try:
        with open(input_file, "r") as f:
            items = json.load(f)
    except FileNotFoundError:
        print(f"{input_file} not found.")
        return
    # High-quality category images
    category_map = {
        "Dairy": "https://images.unsplash.com/photo-1550583724-b2692b85b150?w=400&q=80",
        "Bakery": "https://images.unsplash.com/photo-1509440159596-0249088772ff?w=400&q=80",
        "Instant Food": "https://images.unsplash.com/photo-1612929633738-8fe44f7ec841?w=400&q=80",
        "Staples": "https://images.unsplash.com/photo-1586201375761-83865001e31c?w=400&q=80",
        "Beverages": "https://images.unsplash.com/photo-1527004013197-933c4bcc61f4?w=400&q=80",
        "Snacks": "https://images.unsplash.com/photo-1599490659213-e2b9527bd08c?w=400&q=80",
        "Personal Care": "https://images.unsplash.com/photo-1612817288484-6f916006741a?w=400&q=80",
        "Household": "https://images.unsplash.com/photo-1585421514738-01798e348b17?w=400&q=80",
        "Produce": "https://images.unsplash.com/photo-1610348725531-843dff563e2c?w=400&q=80"
    }
    
    enriched_items = []
    
    for item in items:
        # Override all images with the common category image
        cat = item.get("category", "")
        if cat in category_map:
            item["image"] = category_map[cat]
        else:
            item["image"] = "https://images.unsplash.com/photo-1542838132-92c53300491e?w=400&q=80" # Generic groceries
            
        enriched_items.append(item)


    with open(output_file, "w") as f:
        json.dump(enriched_items, f, indent=2)
    
    print(f"Assigned common category images. Total items processed: {len(enriched_items)}")
    print(f"Saved to {output_file}")


if __name__ == "__main__":
    enrich_data()
