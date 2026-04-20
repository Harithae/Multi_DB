import sys
import os
import random
from datetime import datetime, timezone, timedelta

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import psycopg2
from pymongo import MongoClient
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

def get_pg_conn():
    return psycopg2.connect(
        host=Config.POSTGRES_HOST,
        port=Config.POSTGRES_PORT,
        user=Config.POSTGRES_USER,
        password=Config.POSTGRES_PASSWORD,
        dbname="SalesDB"
    )

def bulk_insert_sales():
    # 1. Fetch MongoDB data
    customers, cust_addr_map = get_mongo_data()
    
    # 2. Generate mock product IDs (since SQL Server isn't available)
    products = list(range(1, 1001))  # Mock 1000 products
    print(f"Using {len(products)} mock product IDs...")
    
    if not customers:
        print("Error: No customers found. Please run customer bulk insert script first.")
        return

    # 3. Connect to PostgreSQL
    conn = get_pg_conn()
    cur = conn.cursor()
    
    print("Cleaning up target PostgreSQL tables...")
    cur.execute('TRUNCATE TABLE Shipments, Invoices, Payments, Order_Items, "Order" RESTART IDENTITY CASCADE')
    conn.commit()

    now_utc = datetime.now(timezone.utc)
    
    print(f"Generating orders for {len(customers)} customers...")
    
    total_orders = 0
    for cust in customers:
        cid = cust["Customer_ID"]
        addr_ids = cust_addr_map.get(cid, [])
        if not addr_ids: 
            continue  # Skip if no address
        
        num_orders = random.randint(5, 10)
        for _ in range(num_orders):
            order_date = now_utc - timedelta(days=random.randint(1, 60))
            aid = random.choice(addr_ids)
            
            # Calculate order items and amount
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
            
            # Insert Order and get ID
            cur.execute(
                'INSERT INTO "Order" (Customer_ID, Customer_Address_ID, Order_Date, Order_Amount, Created_Date) VALUES (%s, %s, %s, %s, %s) RETURNING Order_ID',
                (cid, aid, order_date, order_amount, now_utc)
            )
            order_id = cur.fetchone()[0]
            total_orders += 1
            
            # Insert Order Items
            for item in items_for_order:
                cur.execute(
                    'INSERT INTO Order_Items (Order_ID, Product_ID, Quantity, Price, Created_Date) VALUES (%s, %s, %s, %s, %s)',
                    (order_id, item["Product_ID"], item["Quantity"], item["Price"], now_utc)
                )
            
            # Insert Payment
            pay_method = random.choice(["Credit Card", "PayPal", "Bank Transfer", "Debit Card"])
            pay_status = random.choice(["Completed", "Completed", "Completed", "Pending"])
            cur.execute(
                'INSERT INTO Payments (Order_ID, Payment_Method, Payment_Status, Created_Date) VALUES (%s, %s, %s, %s) RETURNING Payment_ID',
                (order_id, pay_method, pay_status, now_utc)
            )
            payment_id = cur.fetchone()[0]
            
            # Insert Invoice
            cur.execute(
                'INSERT INTO Invoices (Payment_ID, Order_ID, Invoice_Date, Amount, Created_Date) VALUES (%s, %s, %s, %s, %s)',
                (payment_id, order_id, order_date + timedelta(hours=2), order_amount, now_utc)
            )
            
            # Insert Shipment
            ship_status = "Delivered" if pay_status == "Completed" else "Pending"
            deliv_date = order_date + timedelta(days=random.randint(2, 7))
            cur.execute(
                'INSERT INTO Shipments (Shipment_Status, Order_ID, Delivery_Date, Created_Date) VALUES (%s, %s, %s, %s)',
                (ship_status, order_id, deliv_date, now_utc)
            )

    conn.commit()
    conn.close()
    print(f"\n[SUCCESS] Bulk insertion completed!")
    print(f"  Created {total_orders} orders with related items, payments, invoices, and shipments.")

if __name__ == "__main__":
    bulk_insert_sales()
