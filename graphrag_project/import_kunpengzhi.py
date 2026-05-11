#!/usr/bin/env python3
import os
import sys
import json
import hashlib
import traceback
from typing import List, Dict

# Ensure we can import from the root core module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.config import config
from core.database import Database
from core.embeddings import VoyageEmbeddings
from core.utils import chunk_text

SOURCE_DIR = "/home/ben/kunpengzhi"

class KunpengzhiImporter:
    def __init__(self):
        self.embeddings = VoyageEmbeddings()

    def process_markdown_file(self, filepath: str, db: Database):
        filename = os.path.basename(filepath)
        if not os.path.exists(filepath):
            print(f"\n📄 Skipping (not found): {filename}")
            return

        print(f"\n📄 Processing: {filename}")
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        if not content.strip():
            print("   ⚠️  Empty file, skip")
            return

        cursor = db.get_cursor()
        cursor.execute("SELECT id FROM pages WHERE title = %s LIMIT 1", (filename,))
        page = cursor.fetchone()

        if page:
            page_id = page['id']
            print(f"   Found existing page ID: {page_id}")
            cursor.execute("UPDATE pages SET content = %s, updatedAt = NOW() WHERE id = %s", (content, page_id))
        else:
            file_hash = hashlib.md5(filepath.encode()).hexdigest()
            cursor.execute("""
                INSERT INTO pages (path, hash, title, content, contentType, createdAt, updatedAt)
                VALUES (%s, %s, %s, %s, 'markdown', NOW(), NOW())
            """, (filepath, file_hash, filename, content))
            page_id = cursor.lastrowid
            print(f"   Created new page ID: {page_id}")

        db.commit()

        # 文本切分
        chunks = chunk_text(content)
        print(f"   Chunked into {len(chunks)} parts")

        # 删除旧的 chunks
        cursor.execute("DELETE FROM page_chunks WHERE page_id = %s", (page_id,))
        db.commit()

        # 生成向量并保存
        saved_chunks = 0
        for i, chunk in enumerate(chunks):
            if not chunk.strip(): continue
            try:
                embedding = self.embeddings.get_embedding(chunk)
                cursor.execute("""
                    INSERT INTO page_chunks (page_id, chunk_index, content, embedding)
                    VALUES (%s, %s, %s, %s)
                """, (page_id, i, chunk, json.dumps(embedding)))
                saved_chunks += 1
                if (i + 1) % 5 == 0: print(f"     Processed {i+1}/{len(chunks)} chunks...")
            except Exception as e:
                print(f"     ❌ Chunk {i} failed: {e}")

        db.commit()
        print(f"   ✅ Saved {saved_chunks} chunks with embeddings")
        
        # 提取实体关系和标签
        self.extract_and_save_metadata(db, page_id, content, filename)

    def extract_and_save_metadata(self, db: Database, page_id: int, content: str, filename: str):
        # 简单实体提取
        person_keywords = ['希特勒', '丘吉尔', '斯大林', '罗斯福', '蒋介石', '毛泽东']
        location_keywords = ['柏林', '莫斯科', '伦敦', '重庆', '珍珠港', '雅尔塔']
        
        persons = [kw for kw in person_keywords if kw in content]
        locations = [kw for kw in location_keywords if kw in content]
        
        cursor = db.get_cursor(dictionary=False)
        for person in persons:
            for location in locations:
                try:
                    cursor.execute("""
                        INSERT IGNORE INTO entity_relations 
                        (source_entity, source_type, target_entity, target_type, relation_type, page_id, confidence)
                        VALUES (%s, 'person', %s, 'location', 'mentioned_in', %s, 0.8)
                    """, (person, location, page_id))
                except: pass
        
        # 标签提取
        tags = []
        if any(y in filename for y in ['1936', '1937', '1938']): tags.append(('time', '1930s'))
        if '战争' in content or '二战' in content: tags.append(('theme', 'war'))
        
        for category, value in tags:
            cursor.execute("INSERT IGNORE INTO page_tags (page_id, tag_category, tag_value) VALUES (%s, %s, %s)",
                         (page_id, category, value))
        db.commit()

    def run(self):
        print("=" * 80)
        print("Kunpengzhi Import to GraphRAG")
        print("=" * 80)

        with Database() as db:
            md_files = []
            scan_dirs = [("牧人记", os.path.join(SOURCE_DIR, "牧人记"))]

            for dir_name, dir_path in scan_dirs:
                if os.path.exists(dir_path):
                    print(f"Scanning {dir_name}: {dir_path}")
                    for f in os.listdir(dir_path):
                        if f.endswith('.md'):
                            md_files.append((dir_name, os.path.join(dir_path, f)))

            print(f"\nFound {len(md_files)} Markdown files")
            for i, (dir_name, filepath) in enumerate(md_files, 1):
                print(f"\n[{i}/{len(md_files)}] [{dir_name}]")
                try:
                    self.process_markdown_file(filepath, db)
                except Exception as e:
                    print(f"❌ Error processing {filepath}: {e}")
                    traceback.print_exc()

if __name__ == "__main__":
    importer = KunpengzhiImporter()
    importer.run()
