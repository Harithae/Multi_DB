import sys
import os
from datetime import datetime, timezone

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pymongo import MongoClient
from config.db_config import Config

def now():
    return datetime.now(timezone.utc)

def get_db():
    client = MongoClient(Config.MONGODB_URI)
    db = client["CustomerDB"]
    print("Connected to MongoDB. Using database: CustomerDB")
    return db

# ─────────────────────────────────────────────
# Setup: Customer Collection
# ─────────────────────────────────────────────
def setup_customer_collection(db):
    if "Customer" in db.list_collection_names():
        db["Customer"].drop()
        print("Dropped existing 'Customer' collection.")

    db.create_collection("Customer", validator={
        "$jsonSchema": {
            "bsonType": "object",
            "required": ["Customer_ID", "First_Name", "DOB", "Created_Date"],
            "properties": {
                "Customer_ID":   {"bsonType": "int",             "description": "PK - required int"},
                "First_Name":    {"bsonType": "string",          "maxLength": 100},
                "Middle_Name":   {"bsonType": ["string", "null"],"maxLength": 100},
                "Last_Name":     {"bsonType": ["string", "null"],"maxLength": 100},
                "DOB":           {"bsonType": "date",            "description": "Date of Birth - required"},
                "Gender":        {"bsonType": ["string", "null"],"maxLength": 10},
                "Email_ID":      {"bsonType": ["string", "null"],"maxLength": 100},
                "Created_Date":  {"bsonType": "date",            "description": "required"},
                "Modified_Date": {"bsonType": ["date",  "null"]}
            }
        }
    })
    db["Customer"].create_index("Customer_ID", unique=True)
    print("Customer collection created with schema validation & unique index on Customer_ID.")

# ─────────────────────────────────────────────
# Setup: Customer_Address Collection
# ─────────────────────────────────────────────
def setup_customer_address_collection(db):
    if "Customer_Address" in db.list_collection_names():
        db["Customer_Address"].drop()
        print("Dropped existing 'Customer_Address' collection.")

    db.create_collection("Customer_Address", validator={
        "$jsonSchema": {
            "bsonType": "object",
            "required": [
                "Customer_Address_ID", "Customer_ID",
                "City", "State", "Country", "ZIP_Code",
                "Primary_Contact_Number", "Secondary_Contact_Number",
                "Created_Date"
            ],
            "properties": {
                "Customer_Address_ID":       {"bsonType": "int",             "description": "PK - required int"},
                "Customer_ID":               {"bsonType": "int",             "description": "FK → Customer.Customer_ID"},
                "City":                      {"bsonType": "string",          "maxLength": 100},
                "State":                     {"bsonType": "string",          "maxLength": 100},
                "Country":                   {"bsonType": "string",          "maxLength": 100},
                "ZIP_Code":                  {"bsonType": "string",          "maxLength": 20},
                "Primary_Contact_Number":    {"bsonType": "string",          "maxLength": 20},
                "Secondary_Contact_Number":  {"bsonType": "string",          "maxLength": 20},
                "Created_Date":              {"bsonType": "date",            "description": "required"},
                "Modified_Date":             {"bsonType": ["date", "null"]}
            }
        }
    })
    db["Customer_Address"].create_index("Customer_Address_ID", unique=True)
    db["Customer_Address"].create_index("Customer_ID")   # for FK lookups
    print("Customer_Address collection created with schema validation & indexes.")

# ─────────────────────────────────────────────
# Setup: Customer_View_History Collection
# ─────────────────────────────────────────────
def setup_customer_view_history_collection(db):
    if "Customer_View_History" in db.list_collection_names():
        db["Customer_View_History"].drop()
        print("Dropped existing 'Customer_View_History' collection.")
    db.create_collection("Customer_View_History", validator={
        "$jsonSchema": {
            "bsonType": "object",
            "required": ["Customer_View_History_ID", "Customer_ID", "Product_ID", "Product_Price", "Created_Date"],
            "properties": {
                "Customer_View_History_ID": {"bsonType": "int",           "description": "PK - required int"},
                "Customer_ID":             {"bsonType": "int",           "description": "FK -> Customer.Customer_ID"},
                "Product_ID":              {"bsonType": "int",           "description": "required int"},
                "Product_Price":           {"bsonType": "decimal",       "description": "required decimal"},
                "Created_Date":            {"bsonType": "date",          "description": "required"},
                "Modified_Date":           {"bsonType": ["date", "null"]}
            }
        }
    })
    db["Customer_View_History"].create_index("Customer_View_History_ID", unique=True)
    db["Customer_View_History"].create_index("Customer_ID")
    print("Customer_View_History collection created with schema validation & indexes.")

# ─────────────────────────────────────────────
# Setup: Customer_Wish_List Collection
# ─────────────────────────────────────────────
def setup_customer_wish_list_collection(db):
    if "Customer_Wish_List" in db.list_collection_names():
        db["Customer_Wish_List"].drop()
        print("Dropped existing 'Customer_Wish_List' collection.")
    db.create_collection("Customer_Wish_List", validator={
        "$jsonSchema": {
            "bsonType": "object",
            "required": ["Customer_Wish_List_ID", "Wish_List_Name", "Customer_ID", "Created_Date"],
            "properties": {
                "Customer_Wish_List_ID": {"bsonType": "int",    "description": "PK - required int"},
                "Wish_List_Name":        {"bsonType": "string", "maxLength": 100},
                "Customer_ID":           {"bsonType": "int",    "description": "FK -> Customer.Customer_ID"},
                "Created_Date":          {"bsonType": "date",   "description": "required"},
                "Modified_Date":         {"bsonType": ["date", "null"]}
            }
        }
    })
    db["Customer_Wish_List"].create_index("Customer_Wish_List_ID", unique=True)
    db["Customer_Wish_List"].create_index("Customer_ID")
    print("Customer_Wish_List collection created with schema validation & indexes.")

# ─────────────────────────────────────────────
# Setup: Customer_Wish_List_Item Collection
# ─────────────────────────────────────────────
def setup_customer_wish_list_item_collection(db):
    if "Customer_Wish_List_Item" in db.list_collection_names():
        db["Customer_Wish_List_Item"].drop()
        print("Dropped existing 'Customer_Wish_List_Item' collection.")
    db.create_collection("Customer_Wish_List_Item", validator={
        "$jsonSchema": {
            "bsonType": "object",
            "required": ["Customer_Wish_List_Item_ID", "Customer_Wish_List_ID", "Product_ID", "Product_Price", "Created_Date"],
            "properties": {
                "Customer_Wish_List_Item_ID": {"bsonType": "int",     "description": "PK - required int"},
                "Customer_Wish_List_ID":      {"bsonType": "int",     "description": "FK -> Customer_Wish_List.Customer_Wish_List_ID"},
                "Product_ID":                 {"bsonType": "int",     "description": "required int"},
                "Product_Price":              {"bsonType": "decimal", "description": "required decimal"},
                "Created_Date":               {"bsonType": "date",    "description": "required"},
                "Modified_Date":              {"bsonType": ["date", "null"]}
            }
        }
    })
    db["Customer_Wish_List_Item"].create_index("Customer_Wish_List_Item_ID", unique=True)
    db["Customer_Wish_List_Item"].create_index("Customer_Wish_List_ID")
    print("Customer_Wish_List_Item collection created with schema validation & indexes.")

# ─────────────────────────────────────────────
# Print All Data
# ─────────────────────────────────────────────
def print_collection(db, collection_name):
    print(f"\n{'='*50}")
    print(f" Collection: {collection_name}")
    print(f"{'='*50}")
    for doc in db[collection_name].find({}, {"_id": 0}):
        for k, v in doc.items():
            print(f"  {k:<30}: {v}")
        print("-" * 50)

# ─────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────
if __name__ == "__main__":
    print("\n=== CustomerDB Setup ===\n")
    db = get_db()

    print("\n[1/5] Setting up Customer collection...")
    setup_customer_collection(db)

    print("\n[2/5] Setting up Customer_Address collection...")
    setup_customer_address_collection(db)
    
    print("\n[3/5] Setting up Customer_View_History collection...")
    setup_customer_view_history_collection(db)

    print("\n[4/5] Setting up Customer_Wish_List collection...")
    setup_customer_wish_list_collection(db)

    print("\n[5/5] Setting up Customer_Wish_List_Item collection...")
    setup_customer_wish_list_item_collection(db)    

    for col in ["Customer", "Customer_Address", "Customer_View_History", "Customer_Wish_List", "Customer_Wish_List_Item"]:
        print_collection(db, col)

    print("\nCustomerDB setup complete!")
    print("   Collections: Customer, Customer_Address, Customer_View_History, Customer_Wish_List, Customer_Wish_List_Item")
    print("   Database:    CustomerDB")
