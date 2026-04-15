import sys
import os
import random
from datetime import datetime, timezone, timedelta
from bson.decimal128 import Decimal128

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import psycopg2
from psycopg2 import sql, extras
from pymongo import MongoClient
import pyodbc
from config.db_config import Config

def get_mongo_data():
    client = MongoClient(Config.MONGODB_URI)
    db = client["CustomerDB"]
    print("Fetching customers and addresses from MongoDB...")
    
    customers = list(db["Customer"].find({}, {"Customer_ID": 1, "_id": 0}))
    addresses = list(db["Customer_Address"].find({}, {"Customer_Address_ID": 1, "Customer_ID": 1, "_id": 0}))
    
    # Map addresses to customers
    cust_addr_map = {}
    for addr in addresses:
        cid = addr["Customer_ID"]
        if cid not in cust_addr_map:
            cust_addr_map[cid] = []
        cust_addr_map[cid].append(addr["Customer_Address_ID"])
    
    client.close()
    return customers, cust_addr_map

def get_sqlserver_data():
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
    conn_str += "TrustServerCertificate=yes;"
    
    print("Fetching products from SQL Server...")
    conn = pyodbc.connect(conn_str)
    cur = conn.cursor()
    cur.execute("SELECT Product_ID FROM Product")
    products = [row[0] for row in cur.fetchall()]
    conn.close()
    return products

def get_pg_conn():
    return psycopg2.connect(
        host=Config.POSTGRES_HOST,
        port=Config.POSTGRES_PORT,
        user=Config.POSTGRES_USER,
        password=Config.POSTGRES_PASSWORD,
        dbname="SalesDB"
    )

def bulk_insert_sales():
    # 1. Fetch cross-DB data
    customers, cust_addr_map = get_mongo_data()
    products = get_sqlserver_data()
    
    if not customers or not products:
        print("Error: No customers or products found. Please run individual setup/bulk scripts first.")
        return

    # 2. Connect to PG
    conn = get_pg_conn()
    cur = conn.cursor()
    
    print("Cleaning up target PostgreSQL tables...")
    cur.execute('TRUNCATE TABLE Shipments, Invoices, Payments, Order_Items, "Order" RESTART IDENTITY CASCADE')
    conn.commit()

    now_utc = datetime.now(timezone.utc)
    
    all_orders = []
    all_items = []
    all_payments = []
    all_invoices = []
    all_shipments = []

    print(f"Generating orders for {len(customers)} customers...")
    
    for cust in customers:
        cid = cust["Customer_ID"]
        addr_ids = cust_addr_map.get(cid, [])
        if not addr_ids: continue # Skip if no address
        
        num_orders = random.randint(5, 10)
        for _ in range(num_orders):
            order_date = now_utc - timedelta(days=random.randint(1, 60))
            aid = random.choice(addr_ids)
            
            # Temporary state to calculate amount
            items_for_order = []
            order_amount = 0
            num_items = random.randint(1, 5)
            for _ in range(num_items):
                p_id = random.choice(products)
                qty = random.randint(1, 3)
                price = round(random.uniform(20.0, 500.0), 2)
                item_total = price * qty
                order_amount += item_total
                items_for_order.append({
                    "Product_ID": p_id,
                    "Quantity": qty,
                    "Price": price
                })
            
            # Step 1: Insert Order and get ID
            cur.execute(
                'INSERT INTO "Order" (Customer_ID, Customer_Address_ID, Order_Date, Order_Amount, Created_Date) VALUES (%s, %s, %s, %s, %s) RETURNING Order_ID',
                (cid, aid, order_date, order_amount, now_utc)
            )
            order_id = cur.fetchone()[0]
            
            # Step 2: Prepare Items
            for item in items_for_order:
                cur.execute(
                    'INSERT INTO Order_Items (Order_ID, Product_ID, Quantity, Price, Created_Date) VALUES (%s, %s, %s, %s, %s)',
                    (order_id, item["Product_ID"], item["Quantity"], item["Price"], now_utc)
                )
            
            # Step 3: Payments
            pay_method = random.choice(["Credit Card", "PayPal", "Bank Transfer", "Debit Card"])
            pay_status = random.choice(["Completed", "Completed", "Completed", "Pending"]) # Mostly completed
            cur.execute(
                'INSERT INTO Payments (Order_ID, Payment_Method, Payment_Status, Created_Date) VALUES (%s, %s, %s, %s) RETURNING Payment_ID',
                (order_id, pay_method, pay_status, now_utc)
            )
            payment_id = cur.fetchone()[0]
            
            # Step 4: Invoices
            cur.execute(
                'INSERT INTO Invoices (Payment_ID, Order_ID, Invoice_Date, Amount, Created_Date) VALUES (%s, %s, %s, %s, %s)',
                (payment_id, order_id, order_date + timedelta(hours=2), order_amount, now_utc)
            )
            
            # Step 5: Shipments
            ship_status = "Delivered" if pay_status == "Completed" else "Pending"
            deliv_date = order_date + timedelta(days=random.randint(2, 7))
            cur.execute(
                'INSERT INTO Shipments (Shipment_Status, Order_ID, Delivery_Date, Created_Date) VALUES (%s, %s, %s, %s)',
                (ship_status, order_id, deliv_date, now_utc)
            )

    conn.commit()
    conn.close()
    print("\n[SUCCESS] Bulk insertion of Sales system (PostgreSQL) completed!")
    print(f"  Processed ~{len(customers) * 7.5:.0f} orders with related items, payments, invoices, and shipments.")

if __name__ == "__main__":
    bulk_insert_sales()
