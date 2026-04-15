import sys
from config.db_config import Config
from db_managers.postgres_manager import PostgresManager
from db_managers.mongodb_manager import MongoDBManager
from db_managers.sqlserver_manager import SQLServerManager

def main():
    print("Multi-Database Management Tool")
    print("-" * 30)
    print("Initializing Database Managers...")

    # Initialize Managers
    try:
        pg_mgr = PostgresManager(
            Config.POSTGRES_HOST, 
            Config.POSTGRES_PORT, 
            Config.POSTGRES_USER, 
            Config.POSTGRES_PASSWORD, 
            Config.POSTGRES_DB
        )
        print("✓ PostgreSQL Manager Initialized")
    except Exception as e:
        print(f"✗ PostgreSQL Initialization Failed: {e}")
    
    try:
        mongo_mgr = MongoDBManager(Config.MONGODB_URI, Config.MONGODB_DB)
        print("✓ MongoDB Manager Initialized")
    except Exception as e:
        print(f"✗ MongoDB Initialization Failed: {e}")
    
    try:
        is_trusted = Config.SQLSERVER_TRUSTED.lower() == 'yes'
        mssql_mgr = SQLServerManager(
            Config.SQLSERVER_DRIVER, 
            Config.SQLSERVER_SERVER, 
            Config.SQLSERVER_USER, 
            Config.SQLSERVER_PASSWORD, 
            Config.SQLSERVER_DB,
            trusted=is_trusted
        )
        print("✓ SQL Server Manager Initialized")
    except Exception as e:
        print(f"✗ SQL Server Initialization Failed: {e}")

    print("\nAvailable Setup Scripts:")
    print("1. python scripts/setup_customer_mongodb.py   - Setup Customer Database (MongoDB)")
    print("2. python scripts/setup_sales_postgres.py    - Setup Sales Database (PostgreSQL)")
    print("3. python scripts/setup_inventory_sqlserver.py - Setup Inventory Database (SQL Server)")
    
    print("\nUse these managers in your application code for unified database access.")

if __name__ == "__main__":
    main()
