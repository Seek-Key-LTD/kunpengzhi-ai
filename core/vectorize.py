"""
Cloudflare Vectorize RAG — 鲲鹏志语义搜索
=========================================
- 书库 + 历史辩论索引
- bge-m3 多语言 embedding (1024d)
- 向量存 Vectorize, 原文存 R2 JSON 映射
"""

import os
import json
import logging
import uuid
from typing import List, Dict, Optional

log = logging.getLogger("kunpengzhi")

CLOUDFLARE_API_TOKEN = os.getenv("CLOUDFLARE_API_TOKEN", "")
CLOUDFLARE_ACCOUNT_ID = os.getenv("CLOUDFLARE_ACCOUNT_ID", "")
R2_BUCKET = os.getenv("R2_BUCKET", "kunpengzhi-tts")
EMBEDDING_MODEL = "@cf/baai/bge-m3"
INDEX_NAME = "kunpengzhi-books"


def _api_url(path: str) -> str:
    return f"https://api.cloudflare.com/client/v4/accounts/{CLOUDFLARE_ACCOUNT_ID}/{path}"


async def _cf_post(path: str, data: dict) -> dict:
    import httpx
    async with httpx.AsyncClient(timeout=30) as c:
        r = await c.post(
            _api_url(path),
            headers={
                "Authorization": f"Bearer {CLOUDFLARE_API_TOKEN}",
                "Content-Type": "application/json",
            },
            json=data,
        )
        return r.json()


async def _cf_get(path: str) -> dict:
    import httpx
    async with httpx.AsyncClient(timeout=15) as c:
        r = await c.get(
            _api_url(path),
            headers={"Authorization": f"Bearer {CLOUDFLARE_API_TOKEN}"},
        )
        return r.json()


# ─── 原文映射表 (R2) ─────────────────────────────
# Vectorize 查询不返回 metadata, 所以原文存在 R2 JSON 里

RAG_MAP_KEY = "rag/map.json"


async def _load_text_map() -> dict:
    """从 R2 加载 ID→原文 映射"""
    import httpx
    url = (f"https://api.cloudflare.com/client/v4/accounts/{CLOUDFLARE_ACCOUNT_ID}"
           f"/r2/buckets/{R2_BUCKET}/objects/{RAG_MAP_KEY}")
    async with httpx.AsyncClient(timeout=10) as c:
        r = await c.get(url, headers={"Authorization": f"Bearer {CLOUDFLARE_API_TOKEN}"})
        if r.status_code == 200:
            return r.json()
    return {}


async def _save_text_map(map_data: dict) -> bool:
    """保存 ID→原文 映射到 R2"""
    import httpx
    url = (f"https://api.cloudflare.com/client/v4/accounts/{CLOUDFLARE_ACCOUNT_ID}"
           f"/r2/buckets/{R2_BUCKET}/objects/{RAG_MAP_KEY}")
    async with httpx.AsyncClient(timeout=15) as c:
        r = await c.put(
            url,
            headers={"Authorization": f"Bearer {CLOUDFLARE_API_TOKEN}"},
            content=json.dumps(map_data, ensure_ascii=False).encode(),
        )
        return r.status_code == 200 and r.json().get("success", False)


# ─── Embedding ────────────────────────────────────

async def embed(texts: List[str]) -> Optional[List[List[float]]]:
    if not CLOUDFLARE_API_TOKEN or not CLOUDFLARE_ACCOUNT_ID:
        log.warning("Cloudflare not configured")
        return None

    result = await _cf_post(f"ai/run/{EMBEDDING_MODEL}", {"text": texts})
    if result.get("success"):
        data = result["result"]["data"]
        if data and isinstance(data[0], list):
            return data
        return [data]
    log.error(f"Embedding failed: {result.get('errors')}")
    return None


# ─── Vectorize ────────────────────────────────────

async def vectorize_insert(
    vectors: List[List[float]],
    ids: List[str],
    texts: List[str],
    sources: List[str],
) -> bool:
    """批量插入: 向量存 Vectorize, 原文存 R2"""
    if not all([vectors, ids, texts, sources]):
        return False

    # 1. 插入 Vectorize
    vecs = [{"id": vid, "values": vec} for vid, vec in zip(ids, vectors)]
    batch_size = 100
    all_ok = True
    for start in range(0, len(vecs), batch_size):
        batch = vecs[start : start + batch_size]
        result = await _cf_post(
            f"vectorize/v2/indexes/{INDEX_NAME}/insert",
            {"vectors": batch},
        )
        if not result.get("success"):
            log.error(f"Vectorize insert failed: {result.get('errors')}")
            all_ok = False

    # 2. 更新 R2 映射表
    if all_ok:
        text_map = await _load_text_map()
        for vid, txt, src in zip(ids, texts, sources):
            text_map[vid] = {"text": txt, "source": src}
        await _save_text_map(text_map)

    return all_ok


async def vectorize_query(query: str, top_k: int = 5) -> List[dict]:
    """查询 → 返回 [{id, score, text, source}, ...]"""
    emb = await embed([query])
    if not emb:
        return []

    result = await _cf_post(
        f"vectorize/v2/indexes/{INDEX_NAME}/query",
        {"vector": emb[0], "topK": top_k},
    )
    if not result.get("success"):
        log.warning(f"Vectorize query failed: {result.get('errors')}")
        return []

    # 从 R2 映射表查原文
    matches = result["result"].get("matches", [])
    text_map = await _load_text_map()

    results = []
    for m in matches:
        vid = m["id"]
        entry = text_map.get(vid, {})
        results.append({
            "id": vid,
            "score": m["score"],
            "text": entry.get("text", ""),
            "source": entry.get("source", "未知"),
        })
    return results


async def vectorize_info() -> dict:
    result = await _cf_get(f"vectorize/v2/indexes/{INDEX_NAME}")
    return result.get("result", {}) if result.get("success") else {}


# ─── 分块 ────────────────────────────────────────

class Chunker:
    @staticmethod
    def chunk(text: str, max_chars: int = 500, overlap: int = 30) -> List[dict]:
        import re
        paragraphs = re.split(r"\n\n+", text)
        chunks = []
        current = ""
        for para in paragraphs:
            para = para.strip()
            if not para:
                continue
            if len(current) + len(para) > max_chars and current:
                chunks.append({"text": current.strip()})
                current = (current[-overlap:] + "\n\n" + para) if overlap else para
            else:
                current = (current + "\n\n" + para) if current else para
        if current:
            chunks.append({"text": current.strip()})
        return chunks


# ─── 索引管线 ────────────────────────────────────

async def index_sources(sources: Dict[str, str], source_type: str = "book") -> int:
    """索引一批文件到 Vectorize + R2"""
    chunker = Chunker()
    all_texts, all_sources, all_ids = [], [], []
    total = 0

    for title, content in sources.items():
        if not content:
            continue
        for chunk in chunker.chunk(content):
            if len(chunk["text"]) < 20:
                continue
            vid = f"{source_type}_{uuid.uuid4().hex[:12]}"
            all_texts.append(chunk["text"])
            all_sources.append(title)
            all_ids.append(vid)

            if len(all_texts) >= 50:
                vectors = await embed(all_texts)
                if vectors:
                    ok = await vectorize_insert(vectors, all_ids, all_texts, all_sources)
                    if ok:
                        total += len(all_texts)
                all_texts, all_sources, all_ids = [], [], []

    if all_texts:
        vectors = await embed(all_texts)
        if vectors:
            ok = await vectorize_insert(vectors, all_ids, all_texts, all_sources)
            if ok:
                total += len(all_texts)

    log.info(f"✅ Indexed {total} chunks")
    return total


# ─── 辩论用检索接口 ──────────────────────────────

async def get_relevant_chunks(query: str, topic_title: str = "", top_k: int = 8) -> str:
    """一站式：查 Vectorize → 返回 Markdown 格式的相关段落"""
    results = await vectorize_query(query, top_k=top_k)
    if not results:
        return f"（向量搜索无结果）"

    parts = []
    for r in results:
        source = r.get("source", "未知")
        text = r.get("text", "")
        score = r.get("score", 0)
        if text:
            parts.append(f"## 📖 {source} (匹配度: {score:.3f})\n\n{text[:600]}")
    return "\n\n---\n\n".join(parts) if parts else "（无相关段落）"
