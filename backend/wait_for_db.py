import time
import mysql.connector
import os
import sys

def wait_for_db():
    max_retries = 30
    retry_interval = 5
    
    for i in range(max_retries):
        try:
            print(f"Attempting to connect to database... (Attempt {i+1}/{max_retries})")
            connection = mysql.connector.connect(
                    host=os.getenv('MYSQL_HOST', 'db'),
                    database=os.getenv('MYSQL_DB', 'iot_edu'),
                    user=os.getenv('MYSQL_USER', 'IoT_EDU'),
                    password=os.getenv('MYSQL_PASSWORD', 'root'),
                port=3306
            )
            print("✅ MySQL Database is ready!")
            connection.close()
            return True
        except Exception as e:
            print(f"⏳ Waiting for MySQL database... ({i+1}/{max_retries}) - Error: {e}")
            time.sleep(retry_interval)
    
    print("❌ MySQL database connection failed after all retries")
    return False

if __name__ == "__main__":
    success = wait_for_db()
    sys.exit(0 if success else 1)
