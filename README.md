# Multi-Database Management Project

A unified Python project to manage and populate multiple databases (PostgreSQL, MongoDB, and SQL Server) with a focus on relational integrity across different systems.

## 🚀 Features
- **MongoDB (CustomerDB)**: Manages customer profiles, addresses, view history, and wishlists.
- **SQL Server (InventoryDB)**: Manages product categories, products, features, images, and store-wise stock.
- **PostgreSQL (SalesDB)**: Manages e-commerce sales including orders, items, payments, invoices, and shipments, with cross-database references to MongoDB and SQL Server.
- **Unified Managers**: Abstracted database managers for clean, reusable code.

---

## 🛠️ Prerequisites

Ensure you have the following installed:
- **Python 3.8+**
- **PostgreSQL** (running on port 5432)
- **MongoDB** (running on port 27017)
- **SQL Server / LocalDB** (with `(localdb)\MSSQLLocalDB` available)
- **ODBC Driver 17 for SQL Server** (required for `pyodbc`)

---

## 📦 Installation

1. **Clone the repository** (or navigate to the folder):
   ```bash
   cd Multi_DB
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure Environment**:
   Create a `.env` file in the root directory (refer to `.env.example` if available) and update your credentials:
   ```ini
   # PostgreSQL
   POSTGRES_HOST=localhost
   POSTGRES_PORT=5432
   POSTGRES_USER=postgres
   POSTGRES_PASSWORD=your_password
   POSTGRES_DB=postgres

   # MongoDB
   MONGODB_URI=mongodb://localhost:27017/
   MONGODB_DB=CustomerDB

   # SQL Server
   SQLSERVER_DRIVER={ODBC Driver 17 for SQL Server}
   SQLSERVER_SERVER=(localdb)\MSSQLLocalDB
   SQLSERVER_TRUSTED=yes
   SQLSERVER_DB=InventoryDB
   ```

---

## 🏃 Getting Started

Follow these steps in order to set up your environment and populate data.

### Step 1: Initialize Database Schemas
Create the databases and empty table structures.
```bash
python scripts/setup_customer_mongodb.py
python scripts/setup_inventory_sqlserver.py
python scripts/setup_sales_postgres.py
```

### Step 2: Populate Base Data
Insert seed data into the Customer and Inventory systems.
```bash
python scripts/bulk_insert_customer_system.py   # Inserts 100 Customers & Dependencies
python scripts/bulk_insert_inventory_system.py  # Inserts 1,000 Products & Stock
```

### Step 3: Populate Sales Data (Cross-Database)
This script generates orders by pulling valid IDs from MongoDB (Customers) and SQL Server (Products).
```bash
python scripts/bulk_insert_sales_system.py      # Inserts ~750 Orders across all Sales tables
```

### Step 4: Verify Connectivity
Run the main entry point to ensure all database managers are correctly initialized.
```bash
python main.py
```

---

## 📁 Project Structure
- `db_managers/`: Contains the base and specific classes for each database type.
- `scripts/`: Implementation scripts for schema setup and bulk data insertion.
- `config/`: Configuration loader for environment variables.
- `.env`: Local configuration (secrets).
- `main.py`: Project overview and connectivity test.

---

## 📝 Technical Notes
- **Relational Integrity**: Even though data is spread across SQL and NoSQL systems, the scripts ensure `Customer_ID` and `Product_ID` remain consistent across systems.
- **Transactions**: Bulk insertions use transactions (where supported) to ensure data consistency.
- **Decimal Precision**: Financial fields (prices/amounts) use `Decimal128` in MongoDB and `DECIMAL(10,2)` in SQL systems for accuracy.
