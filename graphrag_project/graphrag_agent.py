#!/usr/bin/env python3
import sys
import os
import json
import time
import traceback
from datetime import datetime
from typing import List, Dict, Tuple

# Ensure we can import from the root core module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.config import config
from core.database import Database
from core.embeddings import VoyageEmbeddings
from core.utils import chunk_text
from core.search import graph_rag_search

# ==================== GraphRAG Agent Specific Logic ====================
class GraphRAGAgent:
    def __init__(self):
        self.embeddings = VoyageEmbeddings()

    def run(self):
        print("=" * 80)
        print("GraphRAG Agent Started")
        print(f"Poll interval: {config.POLL_INTERVAL}s")
        print("=" * 80)
        
        while True:
            try:
                with Database() as db:
                    # 获取未处理的页面
                    pages = self.get_unprocessed_pages(db)
                    
                    if pages:
                        print(f"\n[{datetime.now()}] Found {len(pages)} pages to process")
                        for page in pages:
                            try:
                                self.process_page(page, db)
                            except Exception as e:
                                print(f"❌ Error processing page {page['id']}: {e}")
                                traceback.print_exc()
                    else:
                        print(f"[{datetime.now()}] No new pages, waiting...")
                
                # 等待下一轮轮询
                print(f"\n⏳ Next poll in {config.POLL_INTERVAL}s...\n")
                time.sleep(config.POLL_INTERVAL)
                
            except KeyboardInterrupt:
                print("\n\n🛑 Agent stopped by user")
                break
            except Exception as e:
                print(f"\n❌ Fatal error: {e}")
                traceback.print_exc()
                time.sleep(60)

    def get_unprocessed_pages(self, db: Database) -> List[Dict]:
        cursor = db.get_cursor()
        cursor.execute("""
            SELECT p.id, p.title, p.path, p.content, p.updatedAt
            FROM pages p
            LEFT JOIN page_chunks pc ON p.id = pc.page_id
            WHERE p.isPublished = 1
            AND p.content IS NOT NULL
            AND LENGTH(p.content) > 100
            GROUP BY p.id
            HAVING COUNT(pc.id) = 0 
               OR MAX(pc.updated_at) < NOW() - INTERVAL 1 HOUR
            ORDER BY p.updatedAt DESC
            LIMIT 10
        """)
        return cursor.fetchall()

    def process_page(self, page: Dict, db: Database):
        print(f"\n📄 Processing: {page['title']}")
        content = page['content']
        
        # 1. 实体提取
        print("   Extracting entities...")
        extraction_result = self.extract_entities_with_llm(content, page['title'])
        
        # 2. 文本切分
        chunks = chunk_text(content)
        print(f"   Chunked into {len(chunks)} parts")
        
        # 3. 生成向量
        chunk_data = []
        for i, chunk in enumerate(chunks):
            if not chunk.strip(): continue
            try:
                embedding = self.embeddings.get_embedding(chunk)
                chunk_data.append({'index': i, 'content': chunk, 'embedding': embedding})
                print(f"     Chunk {i+1}/{len(chunks)} ✓")
            except Exception as e:
                print(f"     Chunk {i+1} failed: {e}")
        
        # 4. 保存到数据库
        if chunk_data:
            self.save_chunks(db, page['id'], chunk_data)
            print(f"   ✅ Saved {len(chunk_data)} chunks")
        
        if extraction_result['entities']:
            self.save_entities(db, page['id'], extraction_result['entities'])
            print(f"   ✅ Saved {len(extraction_result['entities'])} entity relations")
            
        if extraction_result['tags']:
            self.save_tags(db, page['id'], extraction_result['tags'])
            print(f"   ✅ Saved {len(extraction_result['tags'])} tags")
        
        db.commit()

    def extract_entities_with_llm(self, text: str, title: str) -> Dict:
        """Placeholder for LLM-based entity extraction. Currently rule-based."""
        entities = []
        tags = []
        person_keywords = ['希特勒', '丘吉尔', '斯大林', '罗斯福', '蒋介石', '毛泽东']
        location_keywords = ['柏林', '莫斯科', '伦敦', '重庆', '珍珠港', '雅尔塔']
        
        persons = [kw for kw in person_keywords if kw in text]
        locations = [kw for kw in location_keywords if kw in text]
        
        for person in persons:
            for location in locations:
                entities.append({
                    'source': person, 'source_type': 'person',
                    'target': location, 'target_type': 'location',
                    'relation': 'mentioned_in', 'confidence': 0.8
                })
        
        if any(y in text for y in ['1936', '1937', '1938']): tags.append(('time', '1930s'))
        if '二战' in text or '战争' in text: tags.append(('theme', 'war'))
        
        return {'entities': entities, 'tags': list(set(tags))}

    def save_chunks(self, db: Database, page_id: int, chunks: List[Dict]):
        cursor = db.get_cursor(dictionary=False)
        for chunk in chunks:
            cursor.execute("""
                INSERT INTO page_chunks (page_id, chunk_index, content, embedding)
                VALUES (%s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE 
                    content = VALUES(content),
                    embedding = VALUES(embedding),
                    updated_at = CURRENT_TIMESTAMP
            """, (page_id, chunk['index'], chunk['content'], json.dumps(chunk['embedding'])))

    def save_entities(self, db: Database, page_id: int, entities: List[Dict]):
        cursor = db.get_cursor(dictionary=False)
        for entity in entities:
            cursor.execute("""
                INSERT INTO entity_relations 
                (source_entity, source_type, target_entity, target_type, relation_type, page_id, confidence)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE confidence = VALUES(confidence)
            """, (entity['source'], entity['source_type'], entity['target'], entity['target_type'],
                  entity['relation'], page_id, entity.get('confidence', 0.9)))

    def save_tags(self, db: Database, page_id: int, tags: List[Tuple[str, str]]):
        cursor = db.get_cursor(dictionary=False)
        for category, value in tags:
            cursor.execute("""
                INSERT IGNORE INTO page_tags (page_id, tag_category, tag_value)
                VALUES (%s, %s, %s)
            """, (page_id, category, value))

if __name__ == "__main__":
    agent = GraphRAGAgent()
    agent.run()
