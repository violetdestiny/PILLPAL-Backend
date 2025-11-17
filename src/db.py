import mysql.connector
from mysql.connector import Error

DB_CONFIG = {
    "host": "172.20.10.4",
    "user": "pillpal",
    "password": "Pillpal123",
    "database": "pillpal_db",
    "port": 3306
}

def get_db():
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        return connection
    except Error as e:
        print(f"DB Connection Error: {e}")
        return None
