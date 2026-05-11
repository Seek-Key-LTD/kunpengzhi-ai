import json
import mysql.connector
from core.config import config
from core.database import Database

def test_connection():
    print(f"📡 Testing connection to OCI HeatWave at {config.DB_HOST}...")
    try:
        db = Database()
        print("✅ Connection successful!")
        
        cursor = db.get_cursor()
        
        # 1. Check MySQL Version
        cursor.execute("SELECT VERSION()")
        version = cursor.fetchone()
        print(f"📦 MySQL Version: {version['VERSION()']}")
        
        # 2. Check if VECTOR_DISTANCE function exists
        print("🔍 Checking for VECTOR_DISTANCE support...")
        try:
            # Try a simple vector distance calculation between two 3-dim vectors
            v1 = json.dumps([1.0, 0.0, 0.0])
            v2 = json.dumps([0.0, 1.0, 0.0])
            cursor.execute("SELECT VECTOR_DISTANCE(CAST(%s AS JSON), CAST(%s AS JSON), 'COSINE') as dist", (v1, v2))
            res = cursor.fetchone()
            print(f"🚀 VECTOR_DISTANCE is SUPPORTED! Distance: {res['dist']}")
        except Exception as e:
            print(f"❌ VECTOR_DISTANCE check failed: {e}")
            print("💡 This might mean the HeatWave GenAI plugin is not enabled or the version is < 9.0 (for native) or 8.4 (for some variants).")

        # 3. Check page_chunks table structure
        print("\n📋 Checking 'page_chunks' table...")
        try:
            cursor.execute("DESCRIBE page_chunks")
            columns = cursor.fetchall()
            for col in columns:
                print(f"  - {col['Field']}: {col['Type']}")
        except Exception as e:
            print(f"❌ Could not describe page_chunks: {e}")

    except Exception as e:
        print(f"💥 Connection Failed: {e}")

if __name__ == "__main__":
    test_connection()
