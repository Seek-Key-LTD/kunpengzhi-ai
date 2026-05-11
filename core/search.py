import json
import numpy as np
from typing import List, Dict
from .database import Database
from .embeddings import VoyageEmbeddings

def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    """计算两个向量的余弦相似度"""
    v1 = np.array(vec1)
    v2 = np.array(vec2)
    return np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2))

def get_global_mapping(chapter_name: str) -> str:
    """Retrieve global mapping context using GraphRAG to see where this chapter fits in the 4 books."""
    try:
        with Database() as db:
            cursor = db.get_cursor()
            # Search for the page/chapter metadata across all books
            cursor.execute("""
                SELECT p.title, p.path, COUNT(pc.id) as chunk_count
                FROM pages p
                LEFT JOIN page_chunks pc ON p.id = pc.page_id
                WHERE p.title LIKE %s
                GROUP BY p.id
            """, (f"%{chapter_name}%",))
            
            results = cursor.fetchall()
            if not results:
                return "Global Context: Chapter not found in global mapping."
            
            mapping_info = "📍 **GraphRAG 全局定位 (40万字全景)**:\n"
            for res in results:
                book_name = res['path'].split('/')[-2] if '/' in res['path'] else "未知分册"
                mapping_info += f"- **分册**: {book_name} | **章节**: {res['title']} | **深度**: {res['chunk_count']} 知识点\n"
            
            return mapping_info
    except Exception as e:
        return f"Global Mapping Error: {str(e)}"

def graph_rag_search(query: str, top_k: int = 5) -> Dict:
    """GraphRAG query: utilizes OCI HeatWave Native Vector Search (GenAI)."""
    embeddings = VoyageEmbeddings()
    
    with Database() as db:
        cursor = db.get_cursor()
        
        # 1. Generate query vector locally
        query_embedding = embeddings.get_embedding(query)
        embedding_json = json.dumps(query_embedding)
        
        # 2. OCI HeatWave NATIVE Vector Search
        # Verified syntax for OCI HeatWave 9.x with JSON-stored embeddings:
        # VECTOR_DISTANCE(STRING_TO_VECTOR(CAST(col AS CHAR)), STRING_TO_VECTOR(literal), 'COSINE')
        try:
            cursor.execute("""
                SELECT 
                    pc.page_id,
                    p.title,
                    p.path,
                    pc.chunk_index,
                    pc.content,
                    VECTOR_DISTANCE(
                        STRING_TO_VECTOR(CAST(pc.embedding AS CHAR)), 
                        STRING_TO_VECTOR(%s), 
                        'COSINE'
                    ) as distance
                FROM page_chunks pc
                JOIN pages p ON pc.page_id = p.id
                WHERE p.isPublished = 1
                AND pc.embedding IS NOT NULL
                ORDER BY distance ASC
                LIMIT %s
            """, (embedding_json, top_k))
            vector_results = cursor.fetchall()
            
            # Distance -> Similarity (HeatWave Cosine distance: 0 = same, 1 = orthogonal, 2 = opposite)
            for res in vector_results:
                dist = float(res['distance'] or 1.0)
                res['vector_score'] = 1.0 - dist
                
        except Exception as e:
            # Critical failure: log and raise
            raise RuntimeError(f"OCI HeatWave Vector Search failed: {str(e)}")
        
        # 3. Knowledge Graph Traversal (Entities)
        related_entities = set()
        for result in vector_results:
            cursor.execute("SELECT source_entity, target_entity FROM entity_relations WHERE page_id = %s LIMIT 5", (result['page_id'],))
            for rel in cursor.fetchall():
                related_entities.add(rel['source_entity'])
                related_entities.add(rel['target_entity'])
        
        # 4. Graph results (1-hop)
        graph_results = []
        if related_entities:
            entity_list = list(related_entities)[:10]
            placeholders = ','.join(['%s'] * len(entity_list))
            cursor.execute(f"""
                SELECT er.source_entity, er.relation_type, er.target_entity, er.confidence, p.title as page_title
                FROM entity_relations er
                JOIN pages p ON er.page_id = p.id
                WHERE er.source_entity IN ({placeholders}) OR er.target_entity IN ({placeholders})
                LIMIT 20
            """, entity_list + entity_list)
            graph_results = cursor.fetchall()
    
    return {
        'query': query,
        'vector_results': vector_results,
        'graph_results': graph_results,
        'related_entities': list(related_entities),
        'total_vector_matches': len(vector_results),
        'total_graph_relations': len(graph_results)
    }
