import json
from core.database import Database

def test_real_vector_search():
    db = Database()
    cursor = db.get_cursor()
    
    # Get one real embedding to use as a query
    cursor.execute("SELECT embedding FROM page_chunks WHERE embedding IS NOT NULL LIMIT 1")
    row = cursor.fetchone()
    if not row:
        print("❌ No data in page_chunks!")
        return
        
    embedding_val = row['embedding']
    # If it's stored as JSON string or JSON type, we cast it
    query_json = json.dumps(embedding_val) if not isinstance(embedding_val, str) else embedding_val
    
    print("📡 Running real VECTOR_DISTANCE query on OCI HeatWave...")
    try:
        # Note: Depending on the specific HeatWave setup, pc.embedding might need CAST if it's stored as JSON
        # In MySQL 9.0+, the VECTOR type is preferred, but many RAG systems store as JSON first.
        cursor.execute("""
            SELECT pc.id, p.title, VECTOR_DISTANCE(CAST(pc.embedding AS VECTOR), CAST(%s AS VECTOR), 'COSINE') as dist
            FROM page_chunks pc
            JOIN pages p ON pc.page_id = p.id
            WHERE pc.embedding IS NOT NULL
            LIMIT 3
        """, (query_json,))
        results = cursor.fetchall()
        for res in results:
            print(f"  - Chunk ID: {res['id']}, Dist: {res['dist']}")
        print("✅ Real Vector Search Test PASSED!")
    except Exception as e:
        print(f"❌ Real Vector Search Failed: {e}")

if __name__ == "__main__":
    test_real_vector_search()
