import sys
import os
import random
from datetime import datetime, timezone, timedelta
from bson.decimal128 import Decimal128

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pymongo import MongoClient
from config.db_config import Config

def now():
    return datetime.now(timezone.utc)

def get_db():
    client = MongoClient(Config.MONGODB_URI)
    db = client["CustomerDB"]
    print(f"Connected to MongoDB. Database: CustomerDB")
    return db

def generate_bulk_data(count=100):
    first_names = ["James", "Mary", "Robert", "Patricia", "John", "Jennifer", "Michael", "Linda", "David", "Elizabeth", 
                   "William", "Barbara", "Richard", "Susan", "Joseph", "Jessica", "Thomas", "Sarah", "Charles", "Karen"]
    last_names = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Rodriguez", "Martinez", 
                  "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson", "Thomas", "Taylor", "Moore", "Jackson", "Martin"]
    cities = [("New York", "NY"), ("Los Angeles", "CA"), ("Chicago", "IL"), ("Houston", "TX"), ("Phoenix", "AZ"), 
              ("Philadelphia", "PA"), ("San Antonio", "TX"), ("San Diego", "CA"), ("Dallas", "TX"), ("San Jose", "CA")]
    genders = ["Male", "Female", "Other"]
    
    customers = []
    addresses = []
    histories = []
    wishlists = []
    wishlist_items = []
    
    addr_id_seq = 1
    view_id_seq = 1
    item_id_seq = 1
    
    print(f"Generating data for {count} customers...")
    
    for i in range(1, count + 1):
        cust_id = i
        fname = random.choice(first_names)
        lname = random.choice(last_names)
        mname = random.choice([None, "A.", "B.", "C.", "D."])
        gender = random.choice(genders)
        email = f"{fname.lower()}.{lname.lower()}{cust_id}@example.com"
        dob = datetime(random.randint(1970, 2005), random.randint(1, 12), random.randint(1, 28), tzinfo=timezone.utc)
        
        # 1. Customer
        customers.append({
            "Customer_ID": cust_id,
            "First_Name": fname,
            "Middle_Name": mname,
            "Last_Name": lname,
            "DOB": dob,
            "Gender": gender,
            "Email_ID": email,
            "Created_Date": now(),
            "Modified_Date": None
        })
        
        # 2. Address (at least 1 per customer, some 2)
        num_addr = random.choices([1, 2], weights=[0.8, 0.2])[0]
        for _ in range(num_addr):
            city_info = random.choice(cities)
            addresses.append({
                "Customer_Address_ID": addr_id_seq,
                "Customer_ID": cust_id,
                "City": city_info[0],
                "State": city_info[1],
                "Country": "USA",
                "ZIP_Code": f"{random.randint(10000, 99999)}",
                "Primary_Contact_Number": f"+1-{random.randint(200, 999)}-{random.randint(100, 999)}-{random.randint(1000, 9999)}",
                "Secondary_Contact_Number": f"+1-{random.randint(200, 999)}-{random.randint(100, 999)}-{random.randint(1000, 9999)}",
                "Created_Date": now(),
                "Modified_Date": None
            })
            addr_id_seq += 1
            
        # 3. View History (2-4 per customer)
        for _ in range(random.randint(2, 4)):
            histories.append({
                "Customer_View_History_ID": view_id_seq,
                "Customer_ID": cust_id,
                "Product_ID": random.randint(100, 999),
                "Product_Price": Decimal128(str(round(random.uniform(10.0, 500.0), 2))),
                "Created_Date": now() - timedelta(days=random.randint(1, 30)),
                "Modified_Date": None
            })
            view_id_seq += 1
            
        # 4. Wish List (1 per customer)
        wish_id = cust_id
        wishlists.append({
            "Customer_Wish_List_ID": wish_id,
            "Wish_List_Name": f"{fname}'s Favorites",
            "Customer_ID": cust_id,
            "Created_Date": now(),
            "Modified_Date": None
        })
        
        # 5. Wish List Items (1-3 per wishlist)
        for _ in range(random.randint(1, 3)):
            wishlist_items.append({
                "Customer_Wish_List_Item_ID": item_id_seq,
                "Customer_Wish_List_ID": wish_id,
                "Product_ID": random.randint(100, 999),
                "Product_Price": Decimal128(str(round(random.uniform(10.0, 500.0), 2))),
                "Created_Date": now(),
                "Modified_Date": None
            })
            item_id_seq += 1
            
    return customers, addresses, histories, wishlists, wishlist_items

def bulk_insert():
    db = get_db()
    
    # Generate data
    customers, addresses, histories, wishlists, wishlist_items = generate_bulk_data(100)
    
    # Clear existing data first to ensure clean IDs
    cols = ["Customer", "Customer_Address", "Customer_View_History", "Customer_Wish_List", "Customer_Wish_List_Item"]
    print("\nPre-cleaning collections...")
    for col in cols:
        db[col].delete_many({})
        print(f"Cleaned {col}")

    # Insert data
    print("\nInserting data...")
    try:
        db["Customer"].insert_many(customers)
        print(f"[OK] Inserted {len(customers)} Customers")
        
        db["Customer_Address"].insert_many(addresses)
        print(f"[OK] Inserted {len(addresses)} Addresses")
        
        db["Customer_View_History"].insert_many(histories)
        print(f"[OK] Inserted {len(histories)} View History records")
        
        db["Customer_Wish_List"].insert_many(wishlists)
        print(f"[OK] Inserted {len(wishlists)} Wish Lists")
        
        db["Customer_Wish_List_Item"].insert_many(wishlist_items)
        print(f"[OK] Inserted {len(wishlist_items)} Wish List Items")
        
        print("\nBulk insertion completed successfully!")
    except Exception as e:
        print(f"\n[ERROR] Error during insertion: {e}")

if __name__ == "__main__":
    bulk_insert()
