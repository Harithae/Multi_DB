from abc import ABC, abstractmethod

class BaseManager(ABC):
    @abstractmethod
    def connect(self):
        pass

    @abstractmethod
    def disconnect(self):
        pass

    @abstractmethod
    def create_database(self, db_name):
        pass

    @abstractmethod
    def create_table(self, table_name, schema):
        pass

    @abstractmethod
    def insert_data(self, table_name, data):
        pass

    @abstractmethod
    def execute_query(self, query, params=None):
        pass
