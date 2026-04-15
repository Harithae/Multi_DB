from pymongo import MongoClient
from .base_manager import BaseManager

class MongoDBManager(BaseManager):
    def __init__(self, uri, dbname):
        self.uri = uri
        self.dbname = dbname
        self.client = None
        self.db = None

    def connect(self):
        if not self.client:
            self.client = MongoClient(self.uri)
            self.db = self.client[self.dbname]
        return self.db

    def disconnect(self):
        if self.client:
            self.client.close()
            self.client = None
            self.db = None

    def create_database(self, db_name):
        # In MongoDB, databases are created when data is first inserted.
        # We can just switch to the new database.
        self.connect()
        self.db = self.client[db_name]
        print(f"Switched to MongoDB database '{db_name}'. (Created upon insertion)")

    def create_table(self, table_name, schema=None):
        # In MongoDB, collections are created when data is first inserted.
        # schema is usually not required but can be used for validation if needed.
        self.connect()
        if table_name not in self.db.list_collection_names():
            self.db.create_collection(table_name)
        print(f"MongoDB collection '{table_name}' ensured.")

    def insert_data(self, table_name, data):
        self.connect()
        collection = self.db[table_name]
        if isinstance(data, list):
            collection.insert_many(data)
        else:
            collection.insert_one(data)
        print(f"Inserted data into MongoDB collection '{table_name}'.")

    def execute_query(self, query=None, params=None):
        # query here could be a collection name or a filter
        self.connect()
        # Generic find for demonstration
        if isinstance(query, str):
            collection = self.db[query]
            return list(collection.find(params or {}))
        return None
