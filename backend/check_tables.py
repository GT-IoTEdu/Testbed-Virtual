import os
import MySQLdb
import sys

def check_tables_exist():
    db_config = {
        'host': os.getenv('MYSQL_HOST', 'mysql'),
        'port': 3306,
        'user': os.getenv('MYSQL_USER', 'IoT_EDU'),
        'passwd': os.getenv('MYSQL_PASSWORD', 'sua_senha_mysql_aqui'),
        'db': os.getenv('MYSQL_DB', 'iot_edu'),
    }
    
    required_tables = ['users', 'dhcp_servers', 'dhcp_static_mappings', 'pfsense_aliases']
    
    try:
        conn = MySQLdb.connect(**db_config)
        cursor = conn.cursor()
        
        missing_tables = []
        for table in required_tables:
            cursor.execute("""
                SELECT COUNT(*) FROM information_schema.tables 
                WHERE table_schema = %s AND table_name = %s
            """, (db_config['db'], table))
            
            if cursor.fetchone()[0] == 0:
                missing_tables.append(table)
        
        cursor.close()
        conn.close()
        
        if not missing_tables:
            print("✅ All required database tables are ready!")
            return True
        else:
            print(f"❌ Missing tables: {', '.join(missing_tables)}")
            return False
            
    except Exception as e:
        print(f"❌ Error checking tables: {e}")
        return False

if __name__ == "__main__":
    success = check_tables_exist()
    sys.exit(0 if success else 1)
