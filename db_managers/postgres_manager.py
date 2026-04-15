import psycopg2
from psycopg2 import sql
from .base_manager import BaseManager

class PostgresManager(BaseManager):
    def __init__(self, host, port, user, password, dbname):
        self.config = {
            'host': host,
            'port': port,
            'user': user,
            'password': password,
            'dbname': dbname
        }
        self.conn = None

    def connect(self):
        if not self.conn:
            self.conn = psycopg2.connect(**self.config)
            self.conn.autocommit = True
        return self.conn

    def disconnect(self):
        if self.conn:
            self.conn.close()
            self.conn = None

    def create_database(self, db_name):
        self.connect()
        with self.conn.cursor() as cur:
            cur.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(db_name)))
        print(f"PostgreSQL database '{db_name}' created successfully.")

    def create_table(self, table_name, schema):
        # schema is a string like "id SERIAL PRIMARY KEY, name VARCHAR(100)"
        self.connect()
        with self.conn.cursor() as cur:
            query = f"CREATE TABLE IF NOT EXISTS {table_name} ({schema})"
            cur.execute(query)
        print(f"PostgreSQL table '{table_name}' created successfully.")

    def insert_data(self, table_name, data):
        # data is a list of dictionaries
        if not data:
            return
        self.connect()
        with self.conn.cursor() as cur:
            columns = data[0].keys()
            query = sql.SQL("INSERT INTO {} ({}) VALUES ({})").format(
                sql.Identifier(table_name),
                sql.SQL(', ').join(map(sql.Identifier, columns)),
                sql.SQL(', ').join(sql.Placeholder() * len(columns))
            )
            for row in data:
                cur.execute(query, list(row.values()))
        print(f"Inserted {len(data)} rows into PostgreSQL table '{table_name}'.")

    def execute_query(self, query, params=None):
        self.connect()
        with self.conn.cursor() as cur:
            cur.execute(query, params)
            if cur.description:
                return cur.fetchall()
            return None
