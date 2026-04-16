import sys
import os
import random
from datetime import datetime, timezone, timedelta

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Realistic product names
PRODUCT_NAMES = [
    "Wireless Bluetooth Headphones", "USB-C Charging Cable", "Portable Power Bank", "Smartphone Case",
    "Tempered Glass Screen Protector", "Wireless Mouse", "Mechanical Keyboard", "USB Hub 3.0",
    "Laptop Stand", "Phone Ring Holder", "Screen Cleaner Kit", "Cable Organizer",
    "Webcam HD", "Microphone USB", "Portable SSD 1TB", "HDMI Cable 2.1",
    "Monitor Arm Stand", "Anti-Blue Light Glasses", "Desk Lamp LED", "USB Foot Pedal",
    "Noise-Cancelling Earbuds", "Wireless Charging Pad", "External Hard Drive 2TB", "Car Phone Mount",
    "Desk Organizer", "Keyboard Wrist Rest", "Monitor Light Bar", "Desk Pad Mat",
    "USB Splitter Hub", "Phone Stand Dock", "Wire Manager Clips", "Magnetic Cable Holder"
]

COLORS = ["Black", "White", "Silver", "Gold", "Blue", "Red", "Gray", "Rose Gold"]
SIZES = ["XS", "S", "M", "L", "XL", "XXL", "One Size", "Free Size"]
WEIGHTS = ["100g", "250g", "500g", "1kg", "1.5kg", "2kg", "2.5kg", "3kg"]

import pyodbc
from config.db_config import Config

def get_conn():
    is_trusted = Config.SQLSERVER_TRUSTED.lower() == 'yes'
    conn_str = (
        f"DRIVER={Config.SQLSERVER_DRIVER};"
        f"SERVER={Config.SQLSERVER_SERVER};"
        f"DATABASE=InventoryDB;"
    )
    if is_trusted:
        conn_str += "Trusted_Connection=yes;"
    else:
        conn_str += f"UID={Config.SQLSERVER_USER};PWD={Config.SQLSERVER_PASSWORD};"
    
    conn_str += "TrustServerCertificate=yes;Connection Timeout=60;"
    return pyodbc.connect(conn_str, autocommit=False)

def bulk_insert_inventory(count=1000):
    conn = get_conn()
    cur = conn.cursor()
    now = datetime.now()

    print(f"Starting bulk insertion of {count} products into InventoryDB...")

    try:
        # 1. Clean up existing data first (Reverse FK order)
        print("Cleaning up old data...")
        tables = ["Store_Products", "Store", "Locality", "Product_Features", "Product_Image", "Product", "Product_Category"]
        for t in tables:
            cur.execute(f"DELETE FROM {t}")
        conn.commit()
        print("Old data cleaned.")

        # 2. Insert Categories (50)
        print("Inserting 50 categories...")
        categories = []
        for i in range(1, 51):
            categories.append((f"Category {i}", random.choice(["Male", "Female", "Unisex"]), 0, 99, now))
        
        category_ids = []
        for cat in categories:
            cur.execute("INSERT INTO Product_Category (Product_Category_Name, Target_Gender, Target_Age_Group_From, Target_Age_Group_To, Created_Date) OUTPUT INSERTED.Product_Category_ID VALUES (?,?,?,?,?)", cat)
            category_ids.append(cur.fetchone()[0])

        # 3. Insert Localities (100)
        print("Inserting 100 localities...")
        localities = []
        for i in range(1, 101):
            localities.append((f"Area {i}", f"City {random.randint(1,10)}", "State XYZ", "Country ABC", f"{random.randint(100000,999999)}", now))
        
        locality_ids = []
        for loc in localities:
            cur.execute("INSERT INTO Locality (Area, City, State, Country, ZipCode, Created_Date) OUTPUT INSERTED.Location_ID VALUES (?,?,?,?,?,?)", loc)
            locality_ids.append(cur.fetchone()[0])

        # 4. Insert Stores (200)
        print("Inserting 200 stores...")
        store_ids = []
        for i in range(1, 201):
            loc_id = random.choice(locality_ids)
            store_data = (loc_id, f"Store {i}", f"Address {i}", f"Owner {i}", f"555-{random.randint(100,999)}-{random.randint(1000,9999)}", f"store{i}@example.com", now)
            cur.execute("INSERT INTO Store (Location_ID, Store_Name, Store_Address, Store_Owner_Name, Store_Owner_Phone, Store_Owner_Email, Created_Date) OUTPUT INSERTED.Store_ID VALUES (?,?,?,?,?,?,?)", store_data)
            store_ids.append(cur.fetchone()[0])

        # 5. Insert Products (1000)
        print(f"Inserting {count} products...")
        product_ids = []
        for i in range(1, count + 1):
            cat_id = random.choice(category_ids)
            product_name = random.choice(PRODUCT_NAMES)
            prod_data = (product_name, f"High-quality {product_name.lower()} with excellent features and durability. Perfect for both professional and personal use.", cat_id, now)
            cur.execute("INSERT INTO Product (Product_Name, Product_Description, Product_Category_ID, Created_Date) OUTPUT INSERTED.Product_ID VALUES (?,?,?,?)", prod_data)
            product_ids.append(cur.fetchone()[0])

        # 6. Insert Features (3 per product)
        print("Inserting features...")
        feature_data = []
        for p_id in product_ids:
            # Color feature
            color_val = random.choice(COLORS)
            feature_data.append((p_id, "Color", color_val, now))
            
            # Size feature
            size_val = random.choice(SIZES)
            feature_data.append((p_id, "Size", size_val, now))
            
            # Weight feature
            weight_val = random.choice(WEIGHTS)
            feature_data.append((p_id, "Weight", weight_val, now))
        
        cur.executemany("INSERT INTO Product_Features (Product_ID, Product_Feature_Name, Product_Feature_Value, Created_Date) VALUES (?,?,?,?)", feature_data)

        # 7. Insert Images (1 per product)
        print("Inserting image placeholders...")
        image_data = [(p_id, None, now) for p_id in product_ids]
        cur.executemany("INSERT INTO Product_Image (Product_ID, Product_Image, Created_Date) VALUES (?,?,?)", image_data)

        # 8. Insert Store_Products (Stock for 50% of product-store combinations randomly, capped at 10k)
        print("Inserting stock records...")
        stock_data = []
        # To avoid massive memory/time, let's just do each product in 5-10 random stores
        for p_id in product_ids:
            target_stores = random.sample(store_ids, random.randint(5, 15))
            for s_id in target_stores:
                stock_data.append((s_id, p_id, random.randint(0, 500), now))
        
        # Batch insert to avoid pyodbc character limit issues with massive queries
        batch_size = 1000
        for i in range(0, len(stock_data), batch_size):
            cur.executemany("INSERT INTO Store_Products (Store_ID, Product_ID, Stock_Quantity, Created_Date) VALUES (?,?,?,?)", stock_data[i:i+batch_size])

        conn.commit()
        print("\n[SUCCESS] Bulk insertion of Inventory system completed!")
        print(f"  - Products: {len(product_ids)}")
        print(f"  - Stores: {len(store_ids)}")
        print(f"  - Stock Records: {len(stock_data)}")

    except Exception as e:
        conn.rollback()
        print(f"\n[ERROR] Bulk insertion failed: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    bulk_insert_inventory(1000)
