import sys
import os
from datetime import datetime, timezone, timedelta
import random

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import psycopg2
from psycopg2 import sql
from config.db_config import Config

def get_admin_conn():
    """Connect to default 'postgres' DB to create SalesDB."""
    return psycopg2.connect(
        host=Config.POSTGRES_HOST,
        port=Config.POSTGRES_PORT,
        user=Config.POSTGRES_USER,
        password=Config.POSTGRES_PASSWORD,
        dbname="postgres"
    )

def get_sales_conn():
    """Connect to SalesDB."""
    return psycopg2.connect(
        host=Config.POSTGRES_HOST,
        port=Config.POSTGRES_PORT,
        user=Config.POSTGRES_USER,
        password=Config.POSTGRES_PASSWORD,
        dbname="SalesDB"
    )

# ─────────────────────────────────────────────
# Step 1: Create SalesDB
# ─────────────────────────────────────────────
def create_salesdb():
    conn = get_admin_conn()
    conn.autocommit = True
    with conn.cursor() as cur:
        cur.execute("SELECT 1 FROM pg_database WHERE datname = 'SalesDB'")
        exists = cur.fetchone()
        if exists:
            print("SalesDB already exists, skipping creation.")
        else:
            cur.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier("SalesDB")))
            print("SalesDB created successfully.")
    conn.close()

# ─────────────────────────────────────────────
# Step 2: Create Tables
# ─────────────────────────────────────────────
def create_tables():
    conn = get_sales_conn()
    conn.autocommit = True
    with conn.cursor() as cur:
        # Drop existing tables to apply new schema
        print("Dropping existing tables to refresh schema...")
        cur.execute('DROP TABLE IF EXISTS Shipments, Invoices, Payments, Order_Items, "Order" CASCADE')

        # Order table ("Order" is a reserved word, use double-quotes)
        cur.execute("""
            CREATE TABLE "Order" (
                Order_ID            SERIAL          PRIMARY KEY,
                Customer_ID         INT             NOT NULL,
                Customer_Address_ID INT             NOT NULL,
                Order_Date          TIMESTAMP       NOT NULL,
                Order_Amount        DECIMAL(10,2)   NOT NULL,
                Created_Date        TIMESTAMP       NOT NULL DEFAULT NOW(),
                Modified_Date       TIMESTAMP
            )
        """)
        print("Table 'Order' created.")

        # Order_Items
        cur.execute("""
            CREATE TABLE Order_Items (
                Order_Items_ID  SERIAL          PRIMARY KEY,
                Order_ID        INT             NOT NULL REFERENCES "Order"(Order_ID),
                Product_ID      INT             NOT NULL,
                Quantity        INT             NOT NULL,
                Price           DECIMAL(10,2)  NOT NULL,
                Created_Date    TIMESTAMP       NOT NULL DEFAULT NOW(),
                Modified_Date   TIMESTAMP
            )
        """)
        print("Table 'Order_Items' created.")

        # Payments
        cur.execute("""
            CREATE TABLE Payments (
                Payment_ID      SERIAL          PRIMARY KEY,
                Order_ID        INT             NOT NULL REFERENCES "Order"(Order_ID),
                Payment_Method  VARCHAR(100)    NOT NULL,
                Payment_Status  VARCHAR(100)    NOT NULL,
                Created_Date    TIMESTAMP       NOT NULL DEFAULT NOW(),
                Modified_Date   TIMESTAMP
            )
        """)
        print("Table 'Payments' created.")

        # Invoices
        cur.execute("""
            CREATE TABLE Invoices (
                Invoice_ID      SERIAL          PRIMARY KEY,
                Payment_ID      INT             NOT NULL REFERENCES Payments(Payment_ID),
                Order_ID        INT             NOT NULL REFERENCES "Order"(Order_ID),
                Invoice_Date    TIMESTAMP       NOT NULL,
                Amount          DECIMAL(10,2)  NOT NULL,
                Created_Date    TIMESTAMP       NOT NULL DEFAULT NOW(),
                Modified_Date   TIMESTAMP
            )
        """)
        print("Table 'Invoices' created.")

        # Shipments
        cur.execute("""
            CREATE TABLE Shipments (
                Shipment_ID         SERIAL          PRIMARY KEY,
                Shipment_Status     VARCHAR(100)    NOT NULL,
                Order_ID            INT             NOT NULL REFERENCES "Order"(Order_ID),
                Delivery_Date       TIMESTAMP       NOT NULL,
                Created_Date        TIMESTAMP       NOT NULL DEFAULT NOW(),
                Modified_Date       TIMESTAMP
            )
        """)
        print("Table 'Shipments' created.")

    conn.close()
    print("\nAll tables created in SalesDB.")

# ─────────────────────────────────────────────
# Step 3: Print Data
# ─────────────────────────────────────────────
def print_table(table_name, display_name=None):
    label = display_name or table_name
    conn = get_sales_conn()
    with conn.cursor() as cur:
        cur.execute(f'SELECT * FROM "{table_name}"')
        rows = cur.fetchall()
        cols = [desc[0] for desc in cur.description]
    conn.close()

    print(f"\n{'='*55}")
    print(f"  Table: {label}  ({len(rows)} rows)")
    print(f"{'='*55}")
    col_widths = [max(len(str(c)), max((len(str(r[i])) for r in rows), default=0)) for i, c in enumerate(cols)]
    header = "  " + "  ".join(str(c).ljust(col_widths[i]) for i, c in enumerate(cols))
    print(header)
    print("  " + "-" * (sum(col_widths) + 2 * len(cols)))
    for row in rows:
        print("  " + "  ".join(str(v).ljust(col_widths[i]) for i, v in enumerate(row)))

# ─────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────
if __name__ == "__main__":
    import sys
    mode = sys.argv[1] if len(sys.argv) > 1 else "all"

    if mode == "print":
        # Just print existing data
        print("\n=== SalesDB Data (PostgreSQL) ===")
        for t, d in [("Order","Order"), ("order_items","Order_Items"),
                     ("payments","Payments"), ("invoices","Invoices"), ("shipments","Shipments")]:
            print_table(t, d)
    else:
        print("\n=== SalesDB Setup (PostgreSQL) ===\n")

        print("[1/3] Creating SalesDB...")
        create_salesdb()

        print("\n[2/3] Creating tables...")
        create_tables()

        print("\n[3/3] Printing inserted data...")
        # PostgreSQL lowercases unquoted identifiers; "Order" needs quotes as it's reserved
        for t, d in [("Order","Order"), ("order_items","Order_Items"),
                     ("payments","Payments"), ("invoices","Invoices"), ("shipments","Shipments")]:
            print_table(t, d)

        print("\n\nSalesDB setup complete!")
        print("   Database: SalesDB (PostgreSQL)")
        print("   Tables  : Order, Order_Items, Payments, Invoices, Shipments")
