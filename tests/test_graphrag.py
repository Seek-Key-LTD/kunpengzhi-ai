#!/usr/bin/env python3
"""
GraphRAG查询测试
"""

import sys
sys.path.insert(0, '/home/ben/graphrag_project')

from graphrag_agent import graph_rag_search

def test_graphrag_query():
    print("=" * 80)
    print("GraphRAG Query Test")
    print("=" * 80)
    
    queries = [
        "希特勒和柏林奥运会的关系",
        "二战前的地缘政治格局",
        "丘吉尔在战争中的作用"
    ]
    
    for query in queries:
        print(f"\n🔍 Query: {query}")
        print("-" * 80)
        
        result = graph_rag_search(query, top_k=3)
        
        print(f"\n📊 Vector Search Results ({len(result['vector_results'])}):")
        for i, res in enumerate(result['vector_results'], 1):
            print(f"  {i}. {res['title']}")
            print(f"     Path: {res['path']}")
            print(f"     Preview: {res['content'][:100]}...")
        
        if result['graph_results']:
            print(f"\n🕸️  Graph Expansion Results ({len(result['graph_results'])}):")
            for i, res in enumerate(result['graph_results'][:3], 1):
                print(f"  {i}. {res['title']}")
                print(f"     Entity: {res['source_entity']} → {res['target_entity']}")
                print(f"     Relation: {res['relation_type']}")
        
        if result['related_entities']:
            print(f"\n🔗 Related Entities ({len(result['related_entities'])}):")
            print(f"     {', '.join(result['related_entities'][:10])}")
        
        print("\n" + "=" * 80)

if __name__ == "__main__":
    test_graphrag_query()
