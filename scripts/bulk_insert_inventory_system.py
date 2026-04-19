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

        # 2. Insert Categories (Real Product Categories)
        print("Inserting product categories...")
        category_data = [
            ("Electronics & Gadgets", "Unisex", 15, 65, now),
            ("Accessories", "Unisex", 10, 70, now),
            ("Mobile Devices", "Unisex", 12, 60, now),
            ("Computing", "Unisex", 18, 65, now),
            ("Audio Equipment", "Unisex", 14, 60, now),
            ("Gaming", "Unisex", 8, 50, now),
            ("Smart Home", "Unisex", 20, 65, now),
            ("Wearables", "Unisex", 15, 60, now),
            ("Networking", "Unisex", 20, 65, now),
            ("Storage Devices", "Unisex", 16, 65, now),
            ("Office Supplies", "Unisex", 18, 70, now),
            ("Tech Fashion", "Female", 16, 50, now),
            ("Tech Fashion", "Male", 16, 50, now),
            ("Health & Fitness Trackers", "Unisex", 18, 55, now),
            ("Camera Equipment", "Unisex", 20, 65, now),
            ("USB Cables & Adapters", "Unisex", 12, 70, now),
            ("Screen Protection", "Unisex", 14, 65, now),
            ("Charging Solutions", "Unisex", 15, 70, now),
            ("Desk Accessories", "Unisex", 18, 65, now),
            ("Cable Management", "Unisex", 18, 70, now),
        ]
        
        category_ids = []
        for cat in category_data:
            cur.execute("INSERT INTO Product_Category (Product_Category_Name, Target_Gender, Target_Age_Group_From, Target_Age_Group_To, Created_Date) OUTPUT INSERTED.Product_Category_ID VALUES (?,?,?,?,?)", cat)
            category_ids.append(cur.fetchone()[0])

        # 3. Insert Localities (Real Indian Cities and Areas)
        print("Inserting localities...")
        localities_data = [
            # Bangalore
            ("Whitefield", "Bangalore", "Karnataka", "India", "560066", now),
            ("Koramangala", "Bangalore", "Karnataka", "India", "560034", now),
            ("Indiranagar", "Bangalore", "Karnataka", "India", "560038", now),
            ("MG Road", "Bangalore", "Karnataka", "India", "560001", now),
            ("Marathahalli", "Bangalore", "Karnataka", "India", "560037", now),
            # Mumbai
            ("Bandra", "Mumbai", "Maharashtra", "India", "400050", now),
            ("Andheri", "Mumbai", "Maharashtra", "India", "400053", now),
            ("Powai", "Mumbai", "Maharashtra", "India", "400076", now),
            ("Fort", "Mumbai", "Maharashtra", "India", "400001", now),
            ("Thane", "Mumbai", "Maharashtra", "India", "400601", now),
            # Delhi
            ("Connaught Place", "Delhi", "Delhi", "India", "110001", now),
            ("Noida", "Delhi NCR", "Uttar Pradesh", "India", "201301", now),
            ("Gurgaon", "Delhi NCR", "Haryana", "India", "122001", now),
            ("Dwarka", "Delhi", "Delhi", "India", "110075", now),
            ("South Delhi", "Delhi", "Delhi", "India", "110024", now),
            # Hyderabad
            ("HITEC City", "Hyderabad", "Telangana", "India", "500081", now),
            ("Banjara Hills", "Hyderabad", "Telangana", "India", "500034", now),
            ("Madhapur", "Hyderabad", "Telangana", "India", "500081", now),
            ("Jubilee Hills", "Hyderabad", "Telangana", "India", "500033", now),
            ("Secunderabad", "Hyderabad", "Telangana", "India", "500003", now),
            # Pune
            ("Hinjewadi", "Pune", "Maharashtra", "India", "411057", now),
            ("Viman Nagar", "Pune", "Maharashtra", "India", "411014", now),
            ("Kalyani Nagar", "Pune", "Maharashtra", "India", "411006", now),
            ("Camp", "Pune", "Maharashtra", "India", "411001", now),
            ("Kharadi", "Pune", "Maharashtra", "India", "411014", now),
            # Chennai
            ("T. Nagar", "Chennai", "Tamil Nadu", "India", "600017", now),
            ("Anna Nagar", "Chennai", "Tamil Nadu", "India", "600040", now),
            ("Adyar", "Chennai", "Tamil Nadu", "India", "600020", now),
            ("Mylapore", "Chennai", "Tamil Nadu", "India", "600004", now),
            ("Nungambakkam", "Chennai", "Tamil Nadu", "India", "600034", now),
            # Kolkata
            ("Salt Lake", "Kolkata", "West Bengal", "India", "700064", now),
            ("Ballygunge", "Kolkata", "West Bengal", "India", "700019", now),
            ("AJC Bose Road", "Kolkata", "West Bengal", "India", "700014", now),
            ("Park Street", "Kolkata", "West Bengal", "India", "700016", now),
            ("Rajarhat", "Kolkata", "West Bengal", "India", "700156", now),
            # Jaipur
            ("Vaishali Nagar", "Jaipur", "Rajasthan", "India", "302021", now),
            ("C Scheme", "Jaipur", "Rajasthan", "India", "302001", now),
            ("Malviya Nagar", "Jaipur", "Rajasthan", "India", "302017", now),
            ("Adarsh Nagar", "Jaipur", "Rajasthan", "India", "302004", now),
            ("Tonk Road", "Jaipur", "Rajasthan", "India", "302015", now),
            # Indore
            ("Vijay Nagar", "Indore", "Madhya Pradesh", "India", "452010", now),
            ("Rajwada", "Indore", "Madhya Pradesh", "India", "452002", now),
            ("Bhanwar Kuan", "Indore", "Madhya Pradesh", "India", "452001", now),
            ("South Tukoganj", "Indore", "Madhya Pradesh", "India", "452002", now),
            ("Khajrana", "Indore", "Madhya Pradesh", "India", "452008", now),
            # Lucknow
            ("Gomti Nagar", "Lucknow", "Uttar Pradesh", "India", "226010", now),
            ("Hazratganj", "Lucknow", "Uttar Pradesh", "India", "226001", now),
            ("Aliganj", "Lucknow", "Uttar Pradesh", "India", "226024", now),
            ("Vikas Nagar", "Lucknow", "Uttar Pradesh", "India", "226022", now),
            ("Mahanagar", "Lucknow", "Uttar Pradesh", "India", "226006", now),
        ]
        
        locality_ids = []
        for loc in localities_data:
            cur.execute("INSERT INTO Locality (Area, City, State, Country, ZipCode, Created_Date) OUTPUT INSERTED.Location_ID VALUES (?,?,?,?,?,?)", loc)
            locality_ids.append(cur.fetchone()[0])

        # 4. Insert Stores (Real Store Details)
        print("Inserting 200 stores...")
        store_names = [
            "TechHub Electronics", "Digital World", "Gadget Galaxy", "E-Zone Store", "ElectroMart",
            "Micro Solutions", "Tech Paradise", "Smart Retail", "Connected Store", "Innovation Hub",
            "Digital Express", "Tech Warehouse", "Cyber Store", "Pixel Point", "Tech Central",
            "Modern Electronics", "Future Tech", "ByteShop", "Circuit City", "Tech Arena",
            "Wireless World", "Premium Electronics", "Tech Plus", "Digital Dreams", "Smart Tech",
            "Innovation Store", "Next Gen Tech", "Tech Connect", "Gadget Corner", "Digital Zone",
            "Power Store", "Tech Vision", "Cyber Hub", "Smart Solutions", "Tech Lounge",
            "Digital Mart", "Connected Tech", "Innovation Point", "Tech Bazaar", "Smart Shop",
        ]
        
        owner_names = [
            "Rajesh Kumar", "Priya Singh", "Vikram Patel", "Neha Sharma", "Arjun Desai",
            "Anjali Nair", "Rohit Verma", "Divya Iyer", "Arun Rao", "Meera Reddy",
            "Suresh Kumar", "Shreya Das", "Akshay Gupta", "Pooja Malik", "Nitin Jain",
            "Ananya Chopra", "Harish Reddy", "Kavya Krishnan", "Manish Saxena", "Ritu Pandey",
            "Sanjay Singh", "Deepika Roy", "Rajeev Nair", "Shalini Menon", "Vishal Kapoor",
            "Ritika Sharma", "Aditya Bhatt", "Priyanka Khurana", "Naveen Kumar", "Sneha Verma",
            "Aman Srivastava", "Disha Yadav", "Sameer Khan", "Hina Patel", "Karan Mahajan",
        ]
        
        store_ids = []
        for i in range(1, 201):
            loc_id = random.choice(locality_ids)
            store_name = random.choice(store_names)
            owner_name = random.choice(owner_names)
            phone = f"+91-{random.randint(70,99)}{random.randint(1000,9999)}{random.randint(100000,999999)}"
            email = f"{store_name.lower().replace(' ', '')}{i}@techretail.com"
            address = f"{random.randint(100, 999)} {random.choice(['High Street', 'Main Road', 'Market Lane', 'Shopping Complex', 'Business Centre'])}, {['Unit A', 'Block B', 'Suite C', 'Floor 1', 'Level 2'][i % 5]}"
            
            store_data = (loc_id, store_name, address, owner_name, phone, email, now)
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
