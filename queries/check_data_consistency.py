"""
Check for data consistency and discrepancies across the 3 databases
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pymongo import MongoClient
import psycopg2
import pyodbc
from config.db_config import Config

def check_customer_references():
    """Check if all Customer_IDs in SalesDB exist in CustomerDB"""
    print("\n" + "="*80)
    print("1. Checking Customer References (SalesDB → CustomerDB)")
    print("="*80)
    
    # Get customers from MongoDB
    client = MongoClient(Config.MONGODB_URI)
    db = client["CustomerDB"]
    mongo_customers = set(c["Customer_ID"] for c in db["Customer"].find({}, {"Customer_ID": 1}))
    client.close()
    
    # Get customers from PostgreSQL orders
    conn = psycopg2.connect(
        host=Config.POSTGRES_HOST, port=Config.POSTGRES_PORT,
        user=Config.POSTGRES_USER, password=Config.POSTGRES_PASSWORD,
        dbname="SalesDB"
    )
    cur = conn.cursor()
    cur.execute('SELECT DISTINCT Customer_ID FROM "Order"')
    pg_customers = set(row[0] for row in cur.fetchall())
    conn.close()
    
    missing = pg_customers - mongo_customers
    if missing:
        print(f"   ❌ ISSUE: {len(missing)} Customer_IDs in Orders don't exist in CustomerDB")
        print(f"      Missing IDs: {list(missing)[:10]}")
    else:
        print(f"   ✅ OK: All {len(pg_customers)} customers in orders exist in CustomerDB")

def check_address_references():
    """Check if all Customer_Address_IDs in SalesDB exist in CustomerDB"""
    print("\n" + "="*80)
    print("2. Checking Address References (SalesDB → CustomerDB)")
    print("="*80)
    
    # Get addresses from MongoDB
    client = MongoClient(Config.MONGODB_URI)
    db = client["CustomerDB"]
    mongo_addresses = set(a["Customer_Address_ID"] for a in db["Customer_Address"].find({}, {"Customer_Address_ID": 1}))
    client.close()
    
    # Get addresses from PostgreSQL orders
    conn = psycopg2.connect(
        host=Config.POSTGRES_HOST, port=Config.POSTGRES_PORT,
        user=Config.POSTGRES_USER, password=Config.POSTGRES_PASSWORD,
        dbname="SalesDB"
    )
    cur = conn.cursor()
    cur.execute('SELECT DISTINCT Customer_Address_ID FROM "Order"')
    pg_addresses = set(row[0] for row in cur.fetchall())
    conn.close()
    
    missing = pg_addresses - mongo_addresses
    if missing:
        print(f"   ❌ ISSUE: {len(missing)} Address_IDs in Orders don't exist in CustomerDB")
        print(f"      Missing IDs: {list(missing)[:10]}")
    else:
        print(f"   ✅ OK: All {len(pg_addresses)} addresses in orders exist in CustomerDB")

def check_product_references():
    """Check if all Product_IDs in SalesDB exist in InventoryDB"""
    print("\n" + "="*80)
    print("3. Checking Product References (SalesDB → InventoryDB)")
    print("="*80)
    
    # Get products from SQL Server
    conn_str = (
        f"DRIVER={Config.SQLSERVER_DRIVER};"
        f"SERVER={Config.SQLSERVER_SERVER};"
        f"DATABASE=InventoryDB;"
    )
    if Config.SQLSERVER_TRUSTED.lower() == 'yes':
        conn_str += "Trusted_Connection=yes;"
    else:
        conn_str += f"UID={Config.SQLSERVER_USER};PWD={Config.SQLSERVER_PASSWORD};"
    conn_str += "TrustServerCertificate=yes;"
    
    conn = pyodbc.connect(conn_str)
    cur = conn.cursor()
    cur.execute("SELECT Product_ID FROM Product")
    sql_products = set(row[0] for row in cur.fetchall())
    conn.close()
    
    # Get products from PostgreSQL order items
    conn = psycopg2.connect(
        host=Config.POSTGRES_HOST, port=Config.POSTGRES_PORT,
        user=Config.POSTGRES_USER, password=Config.POSTGRES_PASSWORD,
        dbname="SalesDB"
    )
    cur = conn.cursor()
    cur.execute('SELECT DISTINCT Product_ID FROM Order_Items')
    pg_products = set(row[0] for row in cur.fetchall())
    conn.close()
    
    missing = pg_products - sql_products
    if missing:
        print(f"   ❌ ISSUE: {len(missing)} Product_IDs in Order_Items don't exist in InventoryDB")
        print(f"      Missing IDs: {list(missing)[:10]}")
    else:
        print(f"   ✅ OK: All {len(pg_products)} products in orders exist in InventoryDB")

def check_wishlist_products():
    """Check if Product_IDs in wishlists exist in InventoryDB"""
    print("\n" + "="*80)
    print("4. Checking Wishlist Product References (CustomerDB → InventoryDB)")
    print("="*80)
    
    # Get products from SQL Server
    conn_str = (
        f"DRIVER={Config.SQLSERVER_DRIVER};"
        f"SERVER={Config.SQLSERVER_SERVER};"
        f"DATABASE=InventoryDB;"
    )
    if Config.SQLSERVER_TRUSTED.lower() == 'yes':
        conn_str += "Trusted_Connection=yes;"
    else:
        conn_str += f"UID={Config.SQLSERVER_USER};PWD={Config.SQLSERVER_PASSWORD};"
    conn_str += "TrustServerCertificate=yes;"
    
    conn = pyodbc.connect(conn_str)
    cur = conn.cursor()
    cur.execute("SELECT Product_ID FROM Product")
    sql_products = set(row[0] for row in cur.fetchall())
    conn.close()
    
    # Get products from MongoDB wishlists
    client = MongoClient(Config.MONGODB_URI)
    db = client["CustomerDB"]
    wishlist_products = set(item["Product_ID"] for item in db["Customer_Wish_List_Item"].find({}, {"Product_ID": 1}))
    view_products = set(item["Product_ID"] for item in db["Customer_View_History"].find({}, {"Product_ID": 1}))
    client.close()
    
    missing_wishlist = wishlist_products - sql_products
    missing_views = view_products - sql_products
    
    if missing_wishlist:
        print(f"   ⚠️  WARNING: {len(missing_wishlist)} Product_IDs in wishlists don't exist in InventoryDB")
        print(f"      (This is OK if products were discontinued)")
    else:
        print(f"   ✅ OK: All {len(wishlist_products)} wishlist products exist in InventoryDB")
    
    if missing_views:
        print(f"   ⚠️  WARNING: {len(missing_views)} Product_IDs in view history don't exist in InventoryDB")
    else:
        print(f"   ✅ OK: All {len(view_products)} viewed products exist in InventoryDB")

def check_order_amounts():
    """Check if Order_Amount matches sum of Order_Items"""
    print("\n" + "="*80)
    print("5. Checking Order Amount Calculations (SalesDB)")
    print("="*80)
    
    conn = psycopg2.connect(
        host=Config.POSTGRES_HOST, port=Config.POSTGRES_PORT,
        user=Config.POSTGRES_USER, password=Config.POSTGRES_PASSWORD,
        dbname="SalesDB"
    )
    cur = conn.cursor()
    
    cur.execute("""
        SELECT 
            o.Order_ID,
            o.Order_Amount,
            COALESCE(SUM(oi.Price), 0) as Calculated_Total
        FROM "Order" o
        LEFT JOIN Order_Items oi ON o.Order_ID = oi.Order_ID
        GROUP BY o.Order_ID, o.Order_Amount
        HAVING ABS(o.Order_Amount - COALESCE(SUM(oi.Price), 0)) > 0.01
    """)
    
    mismatches = cur.fetchall()
    conn.close()
    
    if mismatches:
        print(f"   ❌ ISSUE: {len(mismatches)} orders have mismatched amounts")
        for order_id, stored, calculated in mismatches[:5]:
            print(f"      Order {order_id}: Stored=${stored:.2f}, Calculated=${calculated:.2f}")
    else:
        print(f"   ✅ OK: All order amounts match sum of order items")

def check_invoice_amounts():
    """Check if Invoice amounts match Order amounts"""
    print("\n" + "="*80)
    print("6. Checking Invoice Amount Consistency (SalesDB)")
    print("="*80)
    
    conn = psycopg2.connect(
        host=Config.POSTGRES_HOST, port=Config.POSTGRES_PORT,
        user=Config.POSTGRES_USER, password=Config.POSTGRES_PASSWORD,
        dbname="SalesDB"
    )
    cur = conn.cursor()
    
    cur.execute("""
        SELECT 
            i.Invoice_ID,
            i.Order_ID,
            o.Order_Amount,
            i.Amount as Invoice_Amount
        FROM Invoices i
        JOIN "Order" o ON i.Order_ID = o.Order_ID
        WHERE ABS(o.Order_Amount - i.Amount) > 0.01
    """)
    
    mismatches = cur.fetchall()
    conn.close()
    
    if mismatches:
        print(f"   ❌ ISSUE: {len(mismatches)} invoices don't match order amounts")
        for inv_id, ord_id, order_amt, inv_amt in mismatches[:5]:
            print(f"      Invoice {inv_id} (Order {ord_id}): Order=${order_amt:.2f}, Invoice=${inv_amt:.2f}")
    else:
        print(f"   ✅ OK: All invoice amounts match order amounts")

def main():
    print("\n" + "="*80)
    print("DATA CONSISTENCY CHECK ACROSS 3 DATABASES")
    print("="*80)
    
    try:
        check_customer_references()
        check_address_references()
        check_product_references()
        check_wishlist_products()
        check_order_amounts()
        check_invoice_amounts()
        
        print("\n" + "="*80)
        print("CONSISTENCY CHECK COMPLETE")
        print("="*80 + "\n")
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
