"""
知识检索器 — 从鲲鹏志书库中提取辩题相关段落
模拟 Graph RAG 的节点查询效果
"""

import os
import re
import logging
from typing import List, Dict

log = logging.getLogger("kunpengzhi")

# ─── 书库路径 ────────────────────────────────────

BOOK_DIRS = {
    "牧人记": "/home/ben/kunpengzhi/牧人记",
    "双约记": "/home/ben/kunpengzhi/双约记",
    "牧兰记": "/home/ben/kunpengzhi/牧兰记",
    "牧月记": "/home/ben/kunpengzhi/牧月记",
    "digest_彩虹屁": "/home/ben/kunpengzhi/digest/彩虹屁",
    "digest_批判": "/home/ben/kunpengzhi/digest/批判",
}

# Heroku 上从环境变量读取书库路径
HEROKU_BOOK_PATH = os.getenv("KUNPENGZHI_BOOK_PATH", "/app/books")

ON_HEROKU = os.getenv("DYNO") is not None  # 检测是否在 Heroku


class BookRetriever:
    """从书库中检索辩题相关段落"""

    @staticmethod
    def get_content_path() -> str:
        """获取书库根路径"""
        if ON_HEROKU:
            return HEROKU_BOOK_PATH
        return "/home/ben/kunpengzhi"

    @staticmethod
    def load_chapter(book: str, chapter: str) -> str:
        """加载指定章节内容"""
        base = BookRetriever.get_content_path()
        path = os.path.join(base, book, chapter)
        if os.path.exists(path):
            with open(path, "r") as f:
                return f.read()
        return ""

    @staticmethod
    def load_relevant_chapters(topic_id: str) -> Dict[str, str]:
        """
        根据辩题 ID 加载相关章节
        返回: { "章名": "内容", ... }
        """
        base = BookRetriever.get_content_path()

        chapters = {}

        # 辩题 1: 白貂皮 → 第08章
        if topic_id == "1":
            for book in ["牧人记"]:
                ch = os.path.join(base, book, "第08章 半江瑟瑟半江红.md")
                if os.path.exists(ch):
                    with open(ch, "r") as f:
                        chapters["牧人记·第08章 半江瑟瑟半江红"] = f.read()

        # 辩题 2: 木兰的哥哥 → 第07章
        elif topic_id == "2":
            for book in ["牧人记"]:
                ch = os.path.join(base, book, "第07章 木兰无长兄.md")
                if os.path.exists(ch):
                    with open(ch, "r") as f:
                        chapters["牧人记·第07章 木兰无长兄"] = f.read()

        # 辩题 3: 安史之乱 → 相关章节
        elif topic_id == "3":
            # 产权分割/安史之乱相关章节
            for book, ch_name in [
                ("牧人记", '第01章 玉玺：华夏改朝换代的"止血石".md'),
            ]:
                ch = os.path.join(base, book, ch_name)
                if os.path.exists(ch):
                    with open(ch, "r") as f:
                        chapters[f"{book}·{ch_name[:20]}"] = f.read()

        # 也加载彩虹屁和批判
        for dig in ["彩虹屁", "批判"]:
            book_name = {"1": "牧人记", "2": "牧人记", "3": "牧人记"}.get(topic_id, "")
            if book_name:
                dig_path = os.path.join(base, "digest", dig, f"{book_name}-{dig}.md")
                if os.path.exists(dig_path):
                    with open(dig_path, "r") as f:
                        chapters[f"{dig}·{book_name}"] = f.read()

        return chapters

    @staticmethod
    def chunk_text(text: str, max_chars: int = 2000) -> List[str]:
        """将长文本切块"""
        # 按段落切
        paragraphs = re.split(r"\n\n+", text)
        chunks = []
        current = ""
        for p in paragraphs:
            if len(current) + len(p) > max_chars:
                if current:
                    chunks.append(current.strip())
                current = p
            else:
                current += "\n\n" + p
        if current:
            chunks.append(current.strip())
        return chunks

    @staticmethod
    def extract_relevant(
        chapters: Dict[str, str],
        topic: str,
        max_chars: int = 4000,
    ) -> str:
        """
        从加载的章节中提取和辩题相关的关键段落
        返回: markdown 格式的相关内容摘要
        """
        result_parts = []
        for title, content in chapters.items():
            # 简单提取：取前 max_chars 字符
            # 在实际 Graph RAG 中会用 embedding 搜索
            truncated = content[:max_chars]
            result_parts.append(f"## 📖 {title}\n\n{truncated}")

        return "\n\n---\n\n".join(result_parts)


def load_topic_content(topic_id: str, topic_title: str) -> str:
    """
    一站式加载辩题相关书库内容
    返回: 格式化后的参考内容
    """
    retriever = BookRetriever()
    chapters = retriever.load_relevant_chapters(topic_id)
    if not chapters:
        log.warning(f"Topic {topic_id}: no chapters found")
        return f"（未能加载 {topic_title} 相关书库内容）"
    
    log.info(f"Loaded {len(chapters)} chapters for topic {topic_id}")
    return retriever.extract_relevant(chapters, topic_title)
