"""
鲲鹏志 · GraphRAG 简易知识图谱
================================
从三元组构建实体关系图，支持：
1. 实体上下文查询（给定实体，找关联）
2. 辩题全局视角（给定辩题，生成卫星云图）
3. 跨书关联分析
"""

import os
import json
import logging
from collections import defaultdict
from typing import List, Dict, Optional, Tuple

log = logging.getLogger("kunpengzhi")

# 全局图缓存
_graph = None
_entities = None


def load_triples(kg_dir: str = None) -> List[Dict]:
    """加载所有三元组"""
    if kg_dir is None:
        kg_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "outputs", "kg")
    
    triples = []
    for root, dirs, files in os.walk(kg_dir):
        for f in files:
            if f.endswith(".json") and f not in ("full_triples.json", "stats.json", "status.json"):
                try:
                    with open(os.path.join(root, f), encoding="utf-8") as fh:
                        data = json.load(fh)
                        triples.extend(data)
                except:
                    pass
    return triples


def build_graph(triples: List[Dict] = None):
    """构建实体关系图"""
    global _graph, _entities
    
    if triples is None:
        triples = load_triples()
    
    _graph = defaultdict(lambda: {"out": [], "in": []})
    _entities = {}
    
    for t in triples:
        s = t.get("s", "").strip()
        r = t.get("r", "").strip()
        o = t.get("o", "").strip()
        c = t.get("c", "")[:100]  # 上下文片段
        book = t.get("book", "")
        chapter = t.get("chapter", "")
        
        if not s or not o:
            continue
        
        # 正向关系
        _graph[s]["out"].append({"rel": r, "target": o, "context": c, "book": book, "chapter": chapter})
        # 反向关系
        _graph[o]["in"].append({"rel": r, "source": s, "context": c, "book": book, "chapter": chapter})
        
        _entities[s] = _entities.get(s, 0) + 1
        _entities[o] = _entities.get(o, 0) + 1
    
    log.info(f"📊 GraphRAG: {len(triples)} 条边, {len(_entities)} 个节点")
    return _graph


def ensure_graph():
    """确保图已加载"""
    global _graph
    if _graph is None:
        build_graph()
    return _graph


def get_entity_context(entity: str, depth: int = 1, max_results: int = 20) -> Dict:
    """
    获取实体的上下文：直接关联 + 深度扩展
    """
    global _entities
    graph = ensure_graph()
    
    if entity not in graph:
        return {"entity": entity, "direct": [], "expanded": [], "summary": "未找到该实体"}
    
    node = graph[entity]
    direct = node["out"] + node["in"]
    
    mentions = _entities.get(entity, 0) if isinstance(_entities, dict) else 0
    
    result = {
        "entity": entity,
        "mentions": mentions,
        "direct": direct[:max_results],
        "expanded": [],
    }
    
    # 深度扩展
    if depth >= 2:
        expanded_set = set()
        for conn in direct:
            target = conn.get("target") or conn.get("source")
            if target and target in graph:
                for deeper in graph[target]["out"] + graph[target]["in"]:
                    deeper_target = deeper.get("target") or deeper.get("source")
                    if deeper_target and deeper_target != entity and deeper_target not in expanded_set:
                        expanded_set.add(deeper_target)
                        result["expanded"].append(deeper)
        
        result["expanded"] = result["expanded"][:max_results]
    
    # 生成摘要
    relations = set(c["rel"] for c in direct)
    books = set(c["book"] for c in direct if c.get("book"))
    
    summary_parts = [f"「{entity}」在全书中出现 {result['mentions']} 次"]
    if books:
        summary_parts.append(f"涉及 {', '.join(books)}")
    if relations:
        summary_parts.append(f"关联类型: {', '.join(list(relations)[:8])}")
    
    result["summary"] = "。".join(summary_parts)
    
    return result


def get_debate_global_view(topic_title: str, core_concepts: List[str] = None) -> str:
    """
    生成辩题的全局知识图谱视角（卫星云图）
    
    Args:
        topic_title: 辩题标题
        core_concepts: 核心概念列表
    
    Returns:
        人类可读的结构化报告
    """
    graph = ensure_graph()
    
    if core_concepts is None:
        # 从辩题标题提取关键词
        import re
        # 简单的分词：取冒号前后、逗号分隔
        parts = re.split(r'[:：,，]', topic_title)
        core_concepts = [p.strip() for p in parts if len(p.strip()) > 2][:5]
    
    report_parts = ["📡 **全局知识图谱视角**\n"]
    
    for concept in core_concepts:
        ctx = get_entity_context(concept, depth=2)
        if not ctx["direct"]:
            continue
        
        report_parts.append(f"\n### 🔍 「{concept}」的关联网络\n")
        report_parts.append(f"_{ctx['summary']}_\n")
        
        # 按书分组
        books_data = defaultdict(list)
        for c in ctx["direct"]:
            book = c.get("book", "未知")
            rel = c["rel"]
            target = c.get("target") or c.get("source")
            books_data[book].append(f"  → {rel}: {target}")
        
        for book, lines in sorted(books_data.items()):
            report_parts.append(f"📖 **{book}**")
            for line in lines[:5]:
                report_parts.append(line)
            if len(lines) > 5:
                report_parts.append(f"  ... 还有 {len(lines)-5} 条")
            report_parts.append("")
    
    # 交叉连接分析
    report_parts.append("\n### 🔗 跨书连接\n")
    cross_book = defaultdict(list)
    for concept in core_concepts:
        ctx = get_entity_context(concept, depth=1)
        for c in ctx["direct"]:
            book = c.get("book", "未知")
            if book:
                cross_book[book].append(concept)
    
    for book, concepts in sorted(cross_book.items()):
        if len(set(concepts)) > 1:
            report_parts.append(f"📖 **{book}** 同时涉及: {', '.join(set(concepts))}")
    
    if not any(c for c in cross_book.values() if len(set(c)) > 1):
        report_parts.append("（当前数据未发现跨书连接，需要更多三元组）")
    
    report_parts.append("\n---\n*由知识图谱自动生成*")
    
    return "\n".join(report_parts)


def get_top_entities(n: int = 20) -> List[Tuple[str, int]]:
    """获取出现最多的实体"""
    ensure_graph()
    return sorted(_entities.items(), key=lambda x: -x[1])[:n]


def search_entity(query: str) -> List[str]:
    """搜索实体（模糊匹配）"""
    ensure_graph()
    query = query.lower()
    matches = [e for e in _entities if query in e.lower()]
    return matches[:20]
