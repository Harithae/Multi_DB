import sys
import os
from datetime import datetime, timezone, timedelta
import random

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pyodbc
from config.db_config import Config

def get_master_conn():
    """Connect to master DB to create InventoryDB."""
    conn_str = (
        f"DRIVER={Config.SQLSERVER_DRIVER};"
        f"SERVER={Config.SQLSERVER_SERVER};"
        f"DATABASE=master;"
    )
    if Config.SQLSERVER_TRUSTED.lower() == 'yes':
        conn_str += "Trusted_Connection=yes;"
    else:
        conn_str += f"UID={Config.SQLSERVER_USER};PWD={Config.SQLSERVER_PASSWORD};"
    
    conn_str += "TrustServerCertificate=yes;"
    return pyodbc.connect(conn_str, autocommit=True)

def get_inventory_conn(autocommit=False):
    """Connect to InventoryDB."""
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
    conn.autocommit = autocommit
    return conn

# ─────────────────────────────────────────────
# Step 1: Create InventoryDB
# ─────────────────────────────────────────────
def create_inventorydb():
    conn = get_master_conn()
    cur = conn.cursor()
    cur.execute("SELECT name FROM sys.databases WHERE name = 'InventoryDB'")
    if cur.fetchone():
        print("InventoryDB already exists, skipping creation.")
    else:
        cur.execute("CREATE DATABASE InventoryDB")
        print("InventoryDB created successfully.")
    conn.close()

# ─────────────────────────────────────────────
# Step 2: Create Tables (in FK-safe order)
# ─────────────────────────────────────────────
def create_tables():
    conn = get_inventory_conn(autocommit=True)
    cur = conn.cursor()

    # 1. Product_Category (no FKs)
    cur.execute("""
        IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'Product_Category') AND type='U')
        CREATE TABLE Product_Category (
            Product_Category_ID     INT IDENTITY(1,1) PRIMARY KEY,
            Product_Category_Name   VARCHAR(1000)  NOT NULL,
            Target_Gender           VARCHAR(10)    NULL,
            Target_Age_Group_From   INT            NULL,
            Target_Age_Group_To     INT            NULL,
            Created_Date            DATETIME       NOT NULL DEFAULT GETDATE(),
            Modified_Date           DATETIME       NULL
        )
    """)
    print("Table 'Product_Category' created.")

    # 2. Locality (no FKs)
    cur.execute("""
        IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'Locality') AND type='U')
        CREATE TABLE Locality (
            Location_ID     INT IDENTITY(1,1) PRIMARY KEY,
            Area            VARCHAR(100)  NOT NULL,
            City            VARCHAR(100)  NOT NULL,
            State           VARCHAR(100)  NOT NULL,
            Country         VARCHAR(100)  NOT NULL,
            ZipCode         VARCHAR(20)   NOT NULL,
            Created_Date    DATETIME      NOT NULL DEFAULT GETDATE(),
            Modified_Date   DATETIME      NULL
        )
    """)
    print("Table 'Locality' created.")

    # 3. Product (FK → Product_Category)
    # Check if Product_Price column exists in the correct position
    cur.execute("""
        IF EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'Product') AND type='U')
        BEGIN
            -- Check if Product_Price exists but in wrong position (not right after Product_Name)
            IF EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID(N'Product') AND name = 'Product_Price')
            BEGIN
                -- Get column position
                DECLARE @col_position INT
                SELECT @col_position = column_id FROM sys.columns 
                WHERE object_id = OBJECT_ID(N'Product') AND name = 'Product_Price'
                
                -- If Product_Price is not in position 3 (after Product_ID and Product_Name), recreate table
                IF @col_position != 3
                BEGIN
                    -- Drop dependent tables first
                    DROP TABLE IF EXISTS Store_Products
                    DROP TABLE IF EXISTS Product_Features
                    DROP TABLE IF EXISTS Product_Image
                    DROP TABLE IF EXISTS Product
                END
            END
            ELSE
            BEGIN
                -- Product_Price doesn't exist, need to recreate table
                DROP TABLE IF EXISTS Store_Products
                DROP TABLE IF EXISTS Product_Features
                DROP TABLE IF EXISTS Product_Image
                DROP TABLE IF EXISTS Product
            END
        END
    """)
    
    cur.execute("""
        IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'Product') AND type='U')
        CREATE TABLE Product (
            Product_ID              INT IDENTITY(1,1) PRIMARY KEY,
            Product_Name            VARCHAR(1000)  NOT NULL,
            Product_Price           DECIMAL(10,2)  NOT NULL,
            Product_Description     VARCHAR(MAX)   NOT NULL,
            Product_Category_ID     INT            NOT NULL
                REFERENCES Product_Category(Product_Category_ID),
            Created_Date            DATETIME       NOT NULL DEFAULT GETDATE(),
            Modified_Date           DATETIME       NULL
        )
    """)
    print("Table 'Product' created.")

    # 4. Product_Image (FK → Product); BYTE → VARBINARY(MAX)
    cur.execute("""
        IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'Product_Image') AND type='U')
        CREATE TABLE Product_Image (
            Product_Image_ID    INT IDENTITY(1,1) PRIMARY KEY,
            Product_ID          INT              NOT NULL
                REFERENCES Product(Product_ID),
            Product_Image       VARBINARY(MAX)   NULL,
            Created_Date        DATETIME         NOT NULL DEFAULT GETDATE(),
            Modified_Date       DATETIME         NULL
        )
    """)
    print("Table 'Product_Image' created.")

    # 5. Product_Features (FK → Product)
    cur.execute("""
        IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'Product_Features') AND type='U')
        CREATE TABLE Product_Features (
            Product_Feature_ID      INT IDENTITY(1,1) PRIMARY KEY,
            Product_ID              INT           NOT NULL
                REFERENCES Product(Product_ID),
            Product_Feature_Name    VARCHAR(1000) NOT NULL,
            Product_Feature_Value   VARCHAR(1000) NOT NULL,
            Created_Date            DATETIME      NOT NULL DEFAULT GETDATE(),
            Modified_Date           DATETIME      NULL
        )
    """)
    print("Table 'Product_Features' created.")

    # 6. Store (FK → Locality)
    cur.execute("""
        IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'Store') AND type='U')
        CREATE TABLE Store (
            Store_ID            INT IDENTITY(1,1) PRIMARY KEY,
            Location_ID         INT           NOT NULL REFERENCES Locality(Location_ID),
            Store_Name          VARCHAR(200)  NOT NULL,
            Store_Address       VARCHAR(1000) NOT NULL,
            Store_Owner_Name    VARCHAR(200)  NOT NULL,
            Store_Owner_Phone   VARCHAR(20)   NOT NULL,
            Store_Owner_Email   VARCHAR(100)  NOT NULL,
            Created_Date        DATETIME      NOT NULL DEFAULT GETDATE(),
            Modified_Date       DATETIME      NULL
        )
    """)
    print("Table 'Store' created.")

    # 7. Store_Products (FK → Store + Product)
    cur.execute("""
        IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'Store_Products') AND type='U')
        CREATE TABLE Store_Products (
            Store_Products_ID   INT IDENTITY(1,1) PRIMARY KEY,
            Store_ID            INT  NOT NULL REFERENCES Store(Store_ID),
            Product_ID          INT  NOT NULL REFERENCES Product(Product_ID),
            Stock_Quantity      INT  NULL,
            Created_Date        DATETIME NOT NULL DEFAULT GETDATE(),
            Modified_Date       DATETIME NULL
        )
    """)
    print("Table 'Store_Products' created.")

    conn.close()
    print("\nAll 7 tables created in InventoryDB.")

# ─────────────────────────────────────────────
# Step 3: Print Data
# ─────────────────────────────────────────────
def print_table(table_name):
    conn = get_inventory_conn(autocommit=True)
    cur = conn.cursor()
    cur.execute(f"SELECT * FROM {table_name}")
    rows = cur.fetchall()
    cols = [desc[0] for desc in cur.description]
    conn.close()

    print(f"\n{'='*60}")
    print(f"  Table: {table_name}  ({len(rows)} rows)")
    print(f"{'='*60}")
    col_widths = [max(len(str(c)), max((len(str(r[i])[:30]) for r in rows), default=0)) for i, c in enumerate(cols)]
    header = "  " + "  ".join(str(c).ljust(col_widths[i]) for i, c in enumerate(cols))
    print(header)
    print("  " + "-" * (sum(col_widths) + 2 * len(cols)))
    for row in rows:
        print("  " + "  ".join(str(v)[:30].ljust(col_widths[i]) for i, v in enumerate(row)))

# ─────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────
if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "all"

    if mode == "print":
        print("\n=== InventoryDB Data (SQL Server) ===")
        for t in ["Product_Category","Locality","Product","Product_Image",
                  "Product_Features","Store","Store_Products"]:
            print_table(t)
    else:
        print("\n=== InventoryDB Setup (SQL Server) ===\n")

        print("[1/3] Creating InventoryDB...")
        create_inventorydb()

        print("\n[2/3] Creating tables...")
        create_tables()        

        print("\n[3/3] Printing inserted data...")
        for t in ["Product_Category","Locality","Product","Product_Image",
                  "Product_Features","Store","Store_Products"]:
            print_table(t)

        print("\n\nInventoryDB setup complete!")
        print("   Database: InventoryDB (SQL Server)")
        print("   Tables  : Product_Category, Locality, Product, Product_Image,")
        print("             Product_Features, Store, Store_Products")
