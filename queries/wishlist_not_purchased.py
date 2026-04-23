"""
Query: Which products are in customers' wishlists but never purchased?

Cross-DB Query:
- MongoDB (CustomerDB): Get Product_IDs from Customer_Wish_List_Item
- PostgreSQL (SalesDB): Get Product_IDs from Order_Items (purchased products)
- SQL Server (InventoryDB): Get Product details for the difference
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pymongo import MongoClient
import psycopg2
import pyodbc
from config.db_config import Config

def get_wishlist_products():
    """Get all unique Product_IDs from wishlists (MongoDB)"""
    client = MongoClient(Config.MONGODB_URI)
    db = client["CustomerDB"]
    
    wishlist_items = db["Customer_Wish_List_Item"].find({}, {"Product_ID": 1, "_id": 0})
    product_ids = set(item["Product_ID"] for item in wishlist_items)
    
    client.close()
    return product_ids

def get_purchased_products():
    """Get all unique Product_IDs from orders (PostgreSQL)"""
    conn = psycopg2.connect(
        host=Config.POSTGRES_HOST,
        port=Config.POSTGRES_PORT,
        user=Config.POSTGRES_USER,
        password=Config.POSTGRES_PASSWORD,
        dbname="SalesDB"
    )
    
    cur = conn.cursor()
    cur.execute("SELECT DISTINCT Product_ID FROM Order_Items")
    product_ids = set(row[0] for row in cur.fetchall())
    
    conn.close()
    return product_ids

def get_product_details(product_ids):
    """Get product details from SQL Server"""
    if not product_ids:
        return []
    
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
    
    # Convert set to comma-separated string for SQL IN clause
    ids_str = ','.join(str(pid) for pid in product_ids)
    
    query = f"""
        SELECT 
            p.Product_ID,
            p.Product_Name,
            p.Product_Price,
            pc.Product_Category_Name
        FROM Product p
        JOIN Product_Category pc ON p.Product_Category_ID = pc.Product_Category_ID
        WHERE p.Product_ID IN ({ids_str})
        ORDER BY p.Product_Name
    """
    
    cur.execute(query)
    products = []
    for row in cur.fetchall():
        products.append({
            "Product_ID": row[0],
            "Product_Name": row[1],
            "Product_Price": float(row[2]),
            "Category": row[3]
        })
    
    conn.close()
    return products

def main():
    print("\n" + "="*80)
    print("Query: Which products are in customers' wishlists but never purchased?")
    print("="*80 + "\n")
    
    print("Step 1: Fetching wishlist products from MongoDB...")
    wishlist_product_ids = get_wishlist_products()
    print(f"   Found {len(wishlist_product_ids)} unique products in wishlists")
    
    print("\nStep 2: Fetching purchased products from PostgreSQL...")
    purchased_product_ids = get_purchased_products()
    print(f"   Found {len(purchased_product_ids)} unique products purchased")
    
    print("\nStep 3: Finding products in wishlists but NOT purchased...")
    never_purchased_ids = wishlist_product_ids - purchased_product_ids
    print(f"   Found {len(never_purchased_ids)} products in wishlists but never purchased")
    
    if never_purchased_ids:
        print("\nStep 4: Fetching product details from SQL Server...")
        products = get_product_details(never_purchased_ids)
        
        print("\n" + "="*80)
        print("RESULTS: Products in Wishlists but Never Purchased")
        print("="*80 + "\n")
        
        print(f"{'Product ID':<12} {'Product Name':<40} {'Price':<12} {'Category':<20}")
        print("-" * 84)
        
        for p in products:
            print(f"{p['Product_ID']:<12} {p['Product_Name'][:39]:<40} ${p['Product_Price']:<11.2f} {p['Category'][:19]:<20}")
        
        print("\n" + "="*80)
        print(f"Total: {len(products)} products")
        print("="*80 + "\n")
    else:
        print("\nAll wishlist products have been purchased at least once!")

if __name__ == "__main__":
    main()
