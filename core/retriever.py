"""
知识检索器 — 从鲲鹏志书库中提取辩题相关段落
本地优先 → GitHub raw 兜底（Heroku 兼容）
"""

import os
import re
import logging
from typing import List, Dict

log = logging.getLogger("kunpengzhi")

ON_HEROKU = os.getenv("DYNO") is not None


class BookRetriever:
    """从书库中检索辩题相关段落"""

    @staticmethod
    def get_content_path() -> str:
        if ON_HEROKU:
            return os.getenv("KUNPENGZHI_BOOK_PATH", "/app/books")
        return "/home/ben/kunpengzhi"

    @staticmethod
    async def fetch_from_github(path: str, branch: str = "main") -> str:
        """从 GitHub raw 拉取内容"""
        import httpx
        from urllib.parse import quote
        
        # 假设 path 是 "目录/文件名.md" 格式
        parts = path.split('/')
        encoded_parts = [quote(p) for p in parts]
        encoded_path = '/'.join(encoded_parts)
        
        url = f"https://raw.githubusercontent.com/Seek-Key-LTD/kunpengzhi/{branch}/{encoded_path}"
        try:
            async with httpx.AsyncClient(timeout=15) as c:
                r = await c.get(url)
                if r.status_code == 200:
                    return r.text
                log.warning(f"GitHub fetch failed: {url} -> {r.status_code}")
        except Exception as e:
            log.warning(f"GitHub fetch error: {e}")
        return ""

    @staticmethod
    async def load_chapter_remote(book: str, chapter: str, branch: str = "main") -> str:
        """加载章节：本地优先 → GitHub 兜底"""
        base = BookRetriever.get_content_path()
        local = os.path.join(base, book, chapter)
        if os.path.exists(local):
            with open(local, "r") as f:
                return f.read()
        return await BookRetriever.fetch_from_github(f"{book}/{chapter}", branch=branch)

    @staticmethod
    async def load_relevant_chapters(topic_id: str) -> Dict[str, str]:
        """根据辩题 ID 加载相关章节"""
        chapters: Dict[str, str] = {}

        if topic_id == "1":
            ch = await BookRetriever.load_chapter_remote("牧人记", "第08章 半江瑟瑟半江红.md", branch="digest")
            if ch:
                chapters["牧人记·第08章 半江瑟瑟半江红"] = ch

        elif topic_id == "2":
            ch = await BookRetriever.load_chapter_remote("牧人记", "第07章 木兰无长兄.md", branch="digest")
            if ch:
                chapters["牧人记·第07章 木兰无长兄"] = ch

        elif topic_id == "3":
            ch = await BookRetriever.load_chapter_remote("牧人记", '第01章 玉玺：华夏改朝换代的"止血石".md', branch="digest")
            if ch:
                chapters["牧人记·第01章 玉玺"] = ch

        # 彩虹屁 + 批判 (从 digest 分支的 digest/ 目录下加载)
        book_name = {"1": "牧人记", "2": "牧人记", "3": "牧人记"}.get(topic_id, "")
        if book_name:
            for dig in ["彩虹屁", "批判"]:
                text = await BookRetriever.fetch_from_github(
                    f"digest/{dig}/{book_name}-{dig}.md",
                    branch="digest",
                )
                if text:
                    chapters[f"{dig}·{book_name}"] = text

        return chapters

    @staticmethod
    def extract_relevant(chapters: Dict[str, str], max_chars: int = 4000) -> str:
        """格式化输出"""
        parts = []
        for title, content in chapters.items():
            parts.append(f"## 📖 {title}\n\n{content[:max_chars]}")
        return "\n\n---\n\n".join(parts)


async def load_topic_content(topic_id: str) -> str:
    """一站式加载辩题相关书库内容"""
    retriever = BookRetriever()
    chapters = await retriever.load_relevant_chapters(topic_id)
    if not chapters:
        log.warning(f"Topic {topic_id}: no chapters found")
        return ""
    log.info(f"Loaded {len(chapters)} sources for topic {topic_id}")
    return retriever.extract_relevant(chapters)
