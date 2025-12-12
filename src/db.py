import os
import mysql.connector
from mysql.connector import Error
from dotenv import load_dotenv

load_dotenv()

def get_db():
    try:
        conn = mysql.connector.connect(
            host=os.getenv("DB_HOST", "localhost"),
            user=os.getenv("DB_USER", "root"),
            password=os.getenv("DB_PASSWORD", ""),
            database=os.getenv("DB_NAME", "pillpal_db"),
            port=os.getenv("DB_PORT", 3306),  
            autocommit=True
        )
        return conn
    except Error as e:
        print("DB connection error:", e)
        return None
