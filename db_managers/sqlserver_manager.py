import pyodbc
from .base_manager import BaseManager

class SQLServerManager(BaseManager):
    def __init__(self, driver, server, user, password, dbname, trusted=False):
        self.conn_str = (
            f"DRIVER={driver};"
            f"SERVER={server};"
            f"DATABASE={dbname};"
        )
        if trusted:
            self.conn_str += "Trusted_Connection=yes;"
        else:
            self.conn_str += f"UID={user};PWD={password};"
        
        self.conn_str += "TrustServerCertificate=yes;Connection Timeout=30;"
        self.conn = None

    def connect(self):
        if not self.conn:
            self.conn = pyodbc.connect(self.conn_str, autocommit=True)
        return self.conn

    def disconnect(self):
        if self.conn:
            self.conn.close()
            self.conn = None

    def create_database(self, db_name):
        self.connect()
        with self.conn.cursor() as cur:
            cur.execute(f"IF NOT EXISTS (SELECT name FROM sys.databases WHERE name = '{db_name}') CREATE DATABASE {db_name}")
        print(f"SQL Server database '{db_name}' ensured.")

    def create_table(self, table_name, schema):
        self.connect()
        with self.conn.cursor() as cur:
            query = f"IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[{table_name}]') AND type in (N'U')) CREATE TABLE {table_name} ({schema})"
            cur.execute(query)
        print(f"SQL Server table '{table_name}' created successfully.")

    def insert_data(self, table_name, data):
        if not data:
            return
        self.connect()
        with self.conn.cursor() as cur:
            columns = ", ".join(data[0].keys())
            placeholders = ", ".join(["?" for _ in data[0].keys()])
            query = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"
            for row in data:
                cur.execute(query, list(row.values()))
        print(f"Inserted {len(data)} rows into SQL Server table '{table_name}'.")

    def execute_query(self, query, params=None):
        self.connect()
        with self.conn.cursor() as cur:
            if params:
                cur.execute(query, params)
            else:
                cur.execute(query)
            try:
                return cur.fetchall()
            except Exception:
                return None
        return None
