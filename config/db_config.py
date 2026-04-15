import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # PostgreSQL
    POSTGRES_HOST = os.getenv('POSTGRES_HOST', 'localhost')
    POSTGRES_PORT = os.getenv('POSTGRES_PORT', '5432')
    POSTGRES_USER = os.getenv('POSTGRES_USER', 'postgres')
    POSTGRES_PASSWORD = os.getenv('POSTGRES_PASSWORD', 'password')
    POSTGRES_DB = os.getenv('POSTGRES_DB', 'postgres')

    # MongoDB
    MONGODB_URI = os.getenv('MONGODB_URI', 'mongodb://localhost:27017/')
    MONGODB_DB = os.getenv('MONGODB_DB', 'test_db')

    # SQL Server
    SQLSERVER_DRIVER = os.getenv('SQLSERVER_DRIVER', '{ODBC Driver 17 for SQL Server}')
    SQLSERVER_SERVER = os.getenv('SQLSERVER_SERVER', 'localhost')
    SQLSERVER_USER = os.getenv('SQLSERVER_USER', 'sa')
    SQLSERVER_PASSWORD = os.getenv('SQLSERVER_PASSWORD', 'password')
    SQLSERVER_DB = os.getenv('SQLSERVER_DB', 'master')
    SQLSERVER_TRUSTED = os.getenv('SQLSERVER_TRUSTED', 'no')
