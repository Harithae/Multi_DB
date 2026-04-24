import sys
import os
import random
from datetime import datetime, timezone, timedelta

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Category-specific product names for realistic and unique data
CATEGORY_PRODUCTS = {
    "Electronics & Gadgets": [
        "Wireless Bluetooth Headphones", "USB-C Charging Cable", "Portable Power Bank", 
        "Wireless Mouse", "Mechanical Keyboard", "USB Hub 3.0", "Bluetooth Speaker",
        "Smart Watch", "Fitness Tracker", "Wireless Earbuds", "Phone Stand Dock",
        "Digital Photo Frame", "Smart Home Hub", "Voice Assistant", "Wireless Charger"
    ],
    "Mobile Devices": [
        "Smartphone Case", "Tempered Glass Screen Protector", "Car Phone Mount",
        "Wireless Charging Pad", "Phone Ring Holder", "Mobile Game Controller",
        "Selfie Stick Tripod", "Phone Camera Lens Kit", "Mobile Power Bank",
        "Phone Wallet Case", "Magnetic Car Mount", "Phone Grip Stand", "Mobile Cooler Fan"
    ],
    "Computing": [
        "Laptop Stand", "External Hard Drive 1TB", "Wireless Mouse Pad", 
        "USB Webcam HD", "Laptop Cooling Pad", "External DVD Writer",
        "USB Flash Drive 64GB", "Laptop Sleeve Bag", "Wireless Keyboard",
        "Computer Monitor 24inch", "Laptop Docking Station", "PC Speakers", "Webcam Cover"
    ],
    "Camera Equipment": [
        "DSLR Camera Bag", "Camera Tripod Stand", "Memory Card 128GB",
        "Camera Lens Filter", "Flash Speedlight", "Camera Remote Shutter",
        "Lens Cleaning Kit", "Camera Battery Grip", "Photo Studio Light",
        "Camera Strap", "Lens Cap Keeper", "Camera Rain Cover", "Tripod Ball Head"
    ],
    "Gaming": [
        "Gaming Mouse RGB", "Gaming Keyboard Mechanical", "Gaming Headset",
        "Game Controller Wireless", "Gaming Mouse Pad XXL", "Gaming Chair",
        "VR Headset", "Gaming Monitor 27inch", "Gaming Webcam",
        "Gaming Microphone", "Controller Charging Station", "Gaming Desk", "RGB Light Strip"
    ],
    "Networking": [
        "WiFi Router Dual Band", "Ethernet Cable Cat6", "Network Switch 8-Port",
        "WiFi Range Extender", "Powerline Adapter", "Network Cable Tester",
        "Wireless Access Point", "Modem Router Combo", "Network Storage NAS",
        "Fiber Optic Cable", "Network Patch Panel", "WiFi Antenna", "Network Analyzer"
    ],
    "Storage Devices": [
        "Portable SSD 1TB", "External Hard Drive 2TB", "USB Flash Drive 32GB",
        "Memory Card MicroSD", "SSD Internal 500GB", "Hard Drive Enclosure",
        "Cloud Storage Device", "Backup Drive External", "Memory Card Reader",
        "NVMe SSD 1TB", "RAID Enclosure", "USB-C SSD", "Secure USB Drive"
    ],
    "Cable Management": [
        "HDMI Cable 2.1", "USB Extension Cable", "Cable Organizer Box",
        "Cable Clips Adhesive", "Cable Sleeve Wrap", "Power Strip Surge",
        "Cable Ties Velcro", "Cord Management Tray", "Cable Grommet Desk",
        "Wire Raceway", "Cable Spine", "Magnetic Cable Holder", "Under Desk Tray"
    ],
    "Screen Protection": [
        "Screen Cleaner Kit", "Anti-Blue Light Glasses", "Monitor Privacy Filter",
        "Screen Protector Film", "Display Cleaning Wipes", "Screen Guard Liquid",
        "Monitor Stand Riser", "Screen Magnifier Lens", "Display Port Cable",
        "Monitor Light Bar", "Screen Cleaning Cloth", "Privacy Screen 15inch", "Blue Light Filter"
    ],
    "USB Cables & Adapters": [
        "USB-C to USB-A Cable", "Lightning to USB Cable", "USB Splitter Hub",
        "USB-C Adapter Dongle", "Micro USB Cable", "USB Wall Charger",
        "USB Car Charger", "USB Extension Hub", "USB-C Hub Multiport",
        "USB-A to Ethernet", "USB Audio Adapter", "USB-C to HDMI", "Multi-Port USB Hub"
    ],
    "Wearables": [
        "Smart Fitness Band", "Bluetooth Smart Watch", "Heart Rate Monitor",
        "Sleep Tracker Device", "Smart Ring Fitness", "Activity Tracker Kids",
        "GPS Running Watch", "Smart Health Scale", "Posture Tracker Device",
        "Smart Glasses", "Fitness Chest Strap", "Smart Jewelry", "Wearable Camera"
    ],
    "Health & Fitness Trackers": [
        "Blood Pressure Monitor", "Digital Thermometer", "Pulse Oximeter",
        "Body Fat Scale", "Pedometer Step Counter", "Yoga Mat Smart",
        "Resistance Bands Set", "Foam Roller Massage", "Exercise Ball Stability",
        "Smart Water Bottle", "Meditation Headband", "Recovery Massage Gun", "Air Quality Monitor"
    ],
    "Accessories": [
        "Desk Organizer", "Phone Holder Adjustable", "Tablet Stand Foldable",
        "Laptop Riser Stand", "Monitor Arm Mount", "Keyboard Wrist Rest",
        "Mouse Pad Ergonomic", "Cable Management Box", "Desk Lamp LED",
        "Document Camera", "Presentation Remote", "Wireless Presenter", "Desk Fan USB"
    ],
    "Tech Fashion": [
        "Smart Jewelry Ring", "LED Backpack", "Tech Gloves Touchscreen",
        "Smart Clothing Shirt", "Heated Jacket USB", "LED Sneakers",
        "Smart Glasses AR", "Wearable Camera Pin", "Tech Scarf Heated",
        "Smart Belt", "LED Hat", "Heated Gloves", "Smart Socks"
    ]
}

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

        # 3. Insert Localities (US Cities and Neighborhoods)
        print("Inserting localities...")
        localities_data = [
            # New York, NY
            ("Manhattan", "New York", "NY", "USA", "10001", now),
            ("Brooklyn", "New York", "NY", "USA", "11201", now),
            ("Queens", "New York", "NY", "USA", "11354", now),
            ("Bronx", "New York", "NY", "USA", "10451", now),
            ("Staten Island", "New York", "NY", "USA", "10301", now),
            # Los Angeles, CA
            ("Downtown LA", "Los Angeles", "CA", "USA", "90012", now),
            ("Hollywood", "Los Angeles", "CA", "USA", "90028", now),
            ("Santa Monica", "Los Angeles", "CA", "USA", "90401", now),
            ("Beverly Hills", "Los Angeles", "CA", "USA", "90210", now),
            ("Pasadena", "Los Angeles", "CA", "USA", "91101", now),
            # Chicago, IL
            ("The Loop", "Chicago", "IL", "USA", "60601", now),
            ("Lincoln Park", "Chicago", "IL", "USA", "60614", now),
            ("Wicker Park", "Chicago", "IL", "USA", "60622", now),
            ("River North", "Chicago", "IL", "USA", "60654", now),
            ("Hyde Park", "Chicago", "IL", "USA", "60637", now),
            # Houston, TX
            ("Downtown Houston", "Houston", "TX", "USA", "77002", now),
            ("Galleria", "Houston", "TX", "USA", "77056", now),
            ("Midtown", "Houston", "TX", "USA", "77004", now),
            ("The Heights", "Houston", "TX", "USA", "77008", now),
            ("Memorial", "Houston", "TX", "USA", "77024", now),
            # Phoenix, AZ
            ("Downtown Phoenix", "Phoenix", "AZ", "USA", "85003", now),
            ("Scottsdale", "Phoenix", "AZ", "USA", "85251", now),
            ("Tempe", "Phoenix", "AZ", "USA", "85281", now),
            ("Mesa", "Phoenix", "AZ", "USA", "85201", now),
            ("Glendale", "Phoenix", "AZ", "USA", "85301", now),
            # Philadelphia, PA
            ("Center City", "Philadelphia", "PA", "USA", "19102", now),
            ("Old City", "Philadelphia", "PA", "USA", "19106", now),
            ("University City", "Philadelphia", "PA", "USA", "19104", now),
            ("Rittenhouse Square", "Philadelphia", "PA", "USA", "19103", now),
            ("Northern Liberties", "Philadelphia", "PA", "USA", "19123", now),
            # San Antonio, TX
            ("Downtown San Antonio", "San Antonio", "TX", "USA", "78205", now),
            ("Alamo Heights", "San Antonio", "TX", "USA", "78209", now),
            ("Stone Oak", "San Antonio", "TX", "USA", "78258", now),
            ("Southtown", "San Antonio", "TX", "USA", "78204", now),
            ("Medical Center", "San Antonio", "TX", "USA", "78229", now),
            # San Diego, CA
            ("Downtown San Diego", "San Diego", "CA", "USA", "92101", now),
            ("La Jolla", "San Diego", "CA", "USA", "92037", now),
            ("Pacific Beach", "San Diego", "CA", "USA", "92109", now),
            ("Gaslamp Quarter", "San Diego", "CA", "USA", "92101", now),
            ("Mission Valley", "San Diego", "CA", "USA", "92108", now),
            # Dallas, TX
            ("Downtown Dallas", "Dallas", "TX", "USA", "75201", now),
            ("Uptown", "Dallas", "TX", "USA", "75204", now),
            ("Deep Ellum", "Dallas", "TX", "USA", "75226", now),
            ("Highland Park", "Dallas", "TX", "USA", "75205", now),
            ("Bishop Arts District", "Dallas", "TX", "USA", "75208", now),
            # San Jose, CA
            ("Downtown San Jose", "San Jose", "CA", "USA", "95113", now),
            ("Willow Glen", "San Jose", "CA", "USA", "95125", now),
            ("Almaden Valley", "San Jose", "CA", "USA", "95120", now),
            ("Santana Row", "San Jose", "CA", "USA", "95128", now),
            ("Evergreen", "San Jose", "CA", "USA", "95148", now),
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

        # 5. Insert Products (200) - Category-specific products for uniqueness
        print(f"Inserting {count} products...")
        product_ids = []
        
        # Get category names to map with CATEGORY_PRODUCTS
        cur.execute("SELECT Product_Category_ID, Product_Category_Name FROM Product_Category")
        categories = cur.fetchall()
        
        # Calculate products per category (evenly distributed)
        products_per_category = count // len(categories)
        remaining_products = count % len(categories)
        
        # Track used products globally to ensure no duplicates across categories
        used_products_globally = set()
        
        for i, (category_id, category_name) in enumerate(categories):
            # Determine how many products for this category
            products_for_this_cat = products_per_category
            if i < remaining_products:  # Distribute remainder
                products_for_this_cat += 1
            
            # Get category-specific product list, with fallbacks
            available_products = []
            
            # Try exact match first
            if category_name in CATEGORY_PRODUCTS:
                available_products = CATEGORY_PRODUCTS[category_name].copy()
            # Try partial matches for similar categories
            elif "Tech Fashion" in category_name and "Tech Fashion" in CATEGORY_PRODUCTS:
                available_products = CATEGORY_PRODUCTS["Tech Fashion"].copy()
            elif "Gaming" in category_name and "Gaming" in CATEGORY_PRODUCTS:
                available_products = CATEGORY_PRODUCTS["Gaming"].copy()
            elif "Mobile" in category_name and "Mobile Devices" in CATEGORY_PRODUCTS:
                available_products = CATEGORY_PRODUCTS["Mobile Devices"].copy()
            elif "Computing" in category_name and "Computing" in CATEGORY_PRODUCTS:
                available_products = CATEGORY_PRODUCTS["Computing"].copy()
            elif "Audio" in category_name and "Electronics & Gadgets" in CATEGORY_PRODUCTS:
                available_products = CATEGORY_PRODUCTS["Electronics & Gadgets"].copy()
            elif "Wearables" in category_name and "Wearables" in CATEGORY_PRODUCTS:
                available_products = CATEGORY_PRODUCTS["Wearables"].copy()
            elif "Health" in category_name and "Health & Fitness Trackers" in CATEGORY_PRODUCTS:
                available_products = CATEGORY_PRODUCTS["Health & Fitness Trackers"].copy()
            elif "Camera" in category_name and "Camera Equipment" in CATEGORY_PRODUCTS:
                available_products = CATEGORY_PRODUCTS["Camera Equipment"].copy()
            elif "USB" in category_name and "USB Cables & Adapters" in CATEGORY_PRODUCTS:
                available_products = CATEGORY_PRODUCTS["USB Cables & Adapters"].copy()
            elif "Screen" in category_name and "Screen Protection" in CATEGORY_PRODUCTS:
                available_products = CATEGORY_PRODUCTS["Screen Protection"].copy()
            elif "Cable" in category_name and "Cable Management" in CATEGORY_PRODUCTS:
                available_products = CATEGORY_PRODUCTS["Cable Management"].copy()
            elif "Storage" in category_name and "Storage Devices" in CATEGORY_PRODUCTS:
                available_products = CATEGORY_PRODUCTS["Storage Devices"].copy()
            elif "Networking" in category_name and "Networking" in CATEGORY_PRODUCTS:
                available_products = CATEGORY_PRODUCTS["Networking"].copy()
            elif "Accessories" in category_name and "Accessories" in CATEGORY_PRODUCTS:
                available_products = CATEGORY_PRODUCTS["Accessories"].copy()
            else:
                # Fallback to Electronics & Gadgets
                available_products = CATEGORY_PRODUCTS["Electronics & Gadgets"].copy()
            
            # Remove products that have been used globally
            available_products = [p for p in available_products if p not in used_products_globally]
            
            # Generate products for this category
            for j in range(products_for_this_cat):
                if available_products:
                    # Use unique product from category list
                    product_name = available_products.pop(0)
                else:
                    # If we run out, create unique variants
                    base_name = f"Product {category_name.split()[0]}"
                    variant = random.choice(["Pro", "Plus", "Max", "Elite", "Premium", "Advanced", "Deluxe", "Ultra"])
                    product_name = f"{base_name} {variant} {j+1}"
                
                # Ensure global uniqueness
                original_name = product_name
                counter = 1
                while product_name in used_products_globally:
                    product_name = f"{original_name} V{counter}"
                    counter += 1
                
                # Mark as used globally
                used_products_globally.add(product_name)
                
                # Generate realistic price between $199 and $15,999
                product_price = round(random.uniform(199.00, 15999.00), 2)
                prod_data = (product_name, product_price, f"High-quality {product_name.lower()} with excellent features and durability. Perfect for both professional and personal use.", category_id, now)
                cur.execute("INSERT INTO Product (Product_Name, Product_Price, Product_Description, Product_Category_ID, Created_Date) OUTPUT INSERTED.Product_ID VALUES (?,?,?,?,?)", prod_data)
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
    bulk_insert_inventory(200)  # Changed from 1000 to 200
