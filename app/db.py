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
            port=os.getenv("DB_PORT", 3307) # Guys pls change this, my port is 3307 yours is 3306
        )
        return conn
    except Error as e:
        print("DB connection error:", e)
        return None
