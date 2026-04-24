"""
Comprehensive cross-database verification queries for MongoDB, SQL Server, and PostgreSQL
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pymongo import MongoClient
import psycopg2
import pyodbc
from config.db_config import Config

def get_sql_server_conn():
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
    return pyodbc.connect(conn_str)

def get_postgres_conn():
    return psycopg2.connect(
        host=Config.POSTGRES_HOST, port=Config.POSTGRES_PORT,
        user=Config.POSTGRES_USER, password=Config.POSTGRES_PASSWORD,
        dbname="SalesDB"
    )

def get_mongodb_conn():
    client = MongoClient(Config.MONGODB_URI)
    return client["CustomerDB"]

def print_section(title):
    print(f"\n{'='*80}")
    print(f"{title}")
    print(f"{'='*80}")

def query_1_product_consistency():
    """Verify Product_IDs exist across all databases"""
    print_section("1. PRODUCT ID CONSISTENCY ACROSS DATABASES")
    
    # Get Product_IDs from SQL Server
    conn = get_sql_server_conn()
    cur = conn.cursor()
    cur.execute("SELECT Product_ID FROM Product ORDER BY Product_ID")
    sql_products = set(row[0] for row in cur.fetchall())
    conn.close()
    
    # Get Product_IDs from MongoDB
    db = get_mongodb_conn()
    mongo_wishlist_products = set(item["Product_ID"] for item in db["Customer_Wish_List_Item"].find({}, {"Product_ID": 1}))
    mongo_view_products = set(item["Product_ID"] for item in db["Customer_View_History"].find({}, {"Product_ID": 1}))
    
    # Get Product_IDs from PostgreSQL
    conn = get_postgres_conn()
    cur = conn.cursor()
    cur.execute("SELECT DISTINCT Product_ID FROM Order_Items")
    pg_products = set(row[0] for row in cur.fetchall())
    conn.close()
    
    print(f"SQL Server Products: {len(sql_products)} (Range: {min(sql_products)}-{max(sql_products)})")
    print(f"MongoDB Wishlist Products: {len(mongo_wishlist_products)}")
    print(f"MongoDB View History Products: {len(mongo_view_products)}")
    print(f"PostgreSQL Order Products: {len(pg_products)}")
    
    # Check for orphaned references
    orphaned_wishlist = mongo_wishlist_products - sql_products
    orphaned_views = mongo_view_products - sql_products
    orphaned_orders = pg_products - sql_products
    
    if orphaned_wishlist:
        print(f"❌ {len(orphaned_wishlist)} orphaned Product_IDs in wishlists")
    else:
        print("✅ All wishlist Product_IDs exist in inventory")
    
    if orphaned_views:
        print(f"❌ {len(orphaned_views)} orphaned Product_IDs in view history")
    else:
        print("✅ All view history Product_IDs exist in inventory")
    
    if orphaned_orders:
        print(f"❌ {len(orphaned_orders)} orphaned Product_IDs in orders")
    else:
        print("✅ All order Product_IDs exist in inventory")

def query_2_customer_consistency():
    """Verify Customer_IDs exist across MongoDB and PostgreSQL"""
    print_section("2. CUSTOMER ID CONSISTENCY")
    
    # Get Customer_IDs from MongoDB
    db = get_mongodb_conn()
    mongo_customers = set(c["Customer_ID"] for c in db["Customer"].find({}, {"Customer_ID": 1}))
    
    # Get Customer_IDs from PostgreSQL
    conn = get_postgres_conn()
    cur = conn.cursor()
    cur.execute('SELECT DISTINCT Customer_ID FROM "Order"')
    pg_customers = set(row[0] for row in cur.fetchall())
    conn.close()
    
    print(f"MongoDB Customers: {len(mongo_customers)}")
    print(f"PostgreSQL Order Customers: {len(pg_customers)}")
    
    orphaned_customers = pg_customers - mongo_customers
    if orphaned_customers:
        print(f"❌ {len(orphaned_customers)} orphaned Customer_IDs in orders: {list(orphaned_customers)[:10]}")
    else:
        print("✅ All order Customer_IDs exist in CustomerDB")

def query_3_address_consistency():
    """Verify Address_IDs exist across MongoDB and PostgreSQL"""
    print_section("3. ADDRESS ID CONSISTENCY")
    
    # Get Address_IDs from MongoDB
    db = get_mongodb_conn()
    mongo_addresses = set(a["Customer_Address_ID"] for a in db["Customer_Address"].find({}, {"Customer_Address_ID": 1}))
    
    # Get Address_IDs from PostgreSQL
    conn = get_postgres_conn()
    cur = conn.cursor()
    cur.execute('SELECT DISTINCT Customer_Address_ID FROM "Order"')
    pg_addresses = set(row[0] for row in cur.fetchall())
    conn.close()
    
    print(f"MongoDB Addresses: {len(mongo_addresses)}")
    print(f"PostgreSQL Order Addresses: {len(pg_addresses)}")
    
    orphaned_addresses = pg_addresses - mongo_addresses
    if orphaned_addresses:
        print(f"❌ {len(orphaned_addresses)} orphaned Address_IDs in orders: {list(orphaned_addresses)[:10]}")
    else:
        print("✅ All order Address_IDs exist in CustomerDB")

def query_4_location_consistency():
    """Verify location data consistency"""
    print_section("4. LOCATION DATA CONSISTENCY")
    
    # SQL Server locations
    conn = get_sql_server_conn()
    cur = conn.cursor()
    cur.execute("SELECT DISTINCT Country, State, City FROM Locality ORDER BY City")
    sql_locations = set((row[0], row[1], row[2]) for row in cur.fetchall())
    conn.close()
    
    # MongoDB locations
    db = get_mongodb_conn()
    mongo_locations = set()
    for addr in db["Customer_Address"].find({}, {"Country": 1, "State": 1, "City": 1}):
        mongo_locations.add((addr["Country"], addr["State"], addr["City"]))
    
    print(f"SQL Server Locations: {len(sql_locations)}")
    print(f"MongoDB Locations: {len(mongo_locations)}")
    
    # Check for location mismatches
    sql_cities = set(loc[2] for loc in sql_locations)
    mongo_cities = set(loc[2] for loc in mongo_locations)
    
    if sql_cities == mongo_cities:
        print("✅ All cities match between databases")
        print(f"   Cities: {', '.join(sorted(sql_cities))}")
    else:
        print("❌ City mismatch between databases")
        print(f"   SQL only: {sql_cities - mongo_cities}")
        print(f"   MongoDB only: {mongo_cities - sql_cities}")

def query_5_financial_consistency():
    """Verify financial calculations are consistent"""
    print_section("5. FINANCIAL DATA CONSISTENCY")
    
    conn = get_postgres_conn()
    cur = conn.cursor()
    
    # Check Order vs Order_Items totals
    cur.execute("""
        SELECT 
            COUNT(*) as Orders_Checked,
            SUM(CASE WHEN ABS(o.Order_Amount - oi_total.Total) > 0.01 THEN 1 ELSE 0 END) as Mismatched_Orders
        FROM "Order" o
        JOIN (
            SELECT Order_ID, SUM(Price) as Total
            FROM Order_Items 
            GROUP BY Order_ID
        ) oi_total ON o.Order_ID = oi_total.Order_ID
    """)
    
    orders_checked, mismatched_orders = cur.fetchone()
    print(f"Order Amount Verification: {orders_checked} orders checked")
    if mismatched_orders > 0:
        print(f"❌ {mismatched_orders} orders have mismatched amounts")
    else:
        print("✅ All order amounts match sum of order items")
    
    # Check Order vs Invoice totals
    cur.execute("""
        SELECT 
            COUNT(*) as Invoices_Checked,
            SUM(CASE WHEN ABS(o.Order_Amount - i.Amount) > 0.01 THEN 1 ELSE 0 END) as Mismatched_Invoices
        FROM "Order" o
        JOIN Invoices i ON o.Order_ID = i.Order_ID
    """)
    
    invoices_checked, mismatched_invoices = cur.fetchone()
    print(f"Invoice Amount Verification: {invoices_checked} invoices checked")
    if mismatched_invoices > 0:
        print(f"❌ {mismatched_invoices} invoices have mismatched amounts")
    else:
        print("✅ All invoice amounts match order amounts")
    
    conn.close()

def query_6_data_volumes():
    """Show data volumes across all databases"""
    print_section("6. DATA VOLUME SUMMARY")
    
    # SQL Server
    conn = get_sql_server_conn()
    cur = conn.cursor()
    
    print("SQL Server (InventoryDB):")
    tables = [
        ("Product_Category", "Categories"),
        ("Locality", "Locations"), 
        ("Store", "Stores"),
        ("Product", "Products"),
        ("Product_Features", "Product Features"),
        ("Store_Products", "Stock Records")
    ]
    
    for table, label in tables:
        cur.execute(f"SELECT COUNT(*) FROM {table}")
        count = cur.fetchone()[0]
        print(f"   {label}: {count:,}")
    
    conn.close()
    
    # MongoDB
    db = get_mongodb_conn()
    print("\nMongoDB (CustomerDB):")
    collections = [
        ("Customer", "Customers"),
        ("Customer_Address", "Addresses"),
        ("Customer_View_History", "View Records"),
        ("Customer_Wish_List", "Wish Lists"),
        ("Customer_Wish_List_Item", "Wish List Items")
    ]
    
    for collection, label in collections:
        count = db[collection].count_documents({})
        print(f"   {label}: {count:,}")
    
    # PostgreSQL
    conn = get_postgres_conn()
    cur = conn.cursor()
    
    print("\nPostgreSQL (SalesDB):")
    tables = [
        ('"Order"', "Orders"),
        ("Order_Items", "Order Items"),
        ("Payments", "Payments"),
        ("Invoices", "Invoices"),
        ("Shipments", "Shipments")
    ]
    
    for table, label in tables:
        cur.execute(f"SELECT COUNT(*) FROM {table}")
        count = cur.fetchone()[0]
        print(f"   {label}: {count:,}")
    
    conn.close()

def query_7_product_uniqueness():
    """Verify product uniqueness within and across categories"""
    print_section("7. PRODUCT UNIQUENESS VERIFICATION")
    
    conn = get_sql_server_conn()
    cur = conn.cursor()
    
    # Check for duplicate product names globally
    cur.execute("""
        SELECT Product_Name, COUNT(*) as Count
        FROM Product 
        GROUP BY Product_Name
        HAVING COUNT(*) > 1
    """)
    
    global_duplicates = cur.fetchall()
    if global_duplicates:
        print(f"❌ {len(global_duplicates)} product names appear multiple times:")
        for name, count in global_duplicates[:10]:
            print(f"   '{name}': {count} times")
    else:
        print("✅ All product names are globally unique")
    
    # Check for duplicates within categories
    cur.execute("""
        SELECT Product_Category_ID, Product_Name, COUNT(*) as Count
        FROM Product 
        GROUP BY Product_Category_ID, Product_Name
        HAVING COUNT(*) > 1
    """)
    
    category_duplicates = cur.fetchall()
    if category_duplicates:
        print(f"❌ {len(category_duplicates)} products duplicated within categories")
    else:
        print("✅ No duplicate products within categories")
    
    # Show products per category
    cur.execute("""
        SELECT 
            pc.Product_Category_Name,
            COUNT(p.Product_ID) as Product_Count
        FROM Product_Category pc
        LEFT JOIN Product p ON pc.Product_Category_ID = p.Product_Category_ID
        GROUP BY pc.Product_Category_Name
        ORDER BY Product_Count DESC
    """)
    
    print("\nProducts per category:")
    for cat_name, count in cur.fetchall():
        print(f"   {cat_name}: {count}")
    
    conn.close()

def main():
    print("\n" + "="*80)
    print("COMPREHENSIVE CROSS-DATABASE VERIFICATION")
    print("="*80)
    
    try:
        query_1_product_consistency()
        query_2_customer_consistency()
        query_3_address_consistency()
        query_4_location_consistency()
        query_5_financial_consistency()
        query_6_data_volumes()
        query_7_product_uniqueness()
        
        print_section("VERIFICATION COMPLETE")
        print("All cross-database consistency checks finished!")
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()