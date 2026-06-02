"""
鲲鹏志书库 → Cloudflare Vectorize 索引
运行: python scripts/index_books.py
"""

import asyncio
import sys
import os

# 把项目根目录加到 path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.vectorize import index_sources, vectorize_info
from core.retriever import BookRetriever, ON_HEROKU


async def main():
    print("=" * 50)
    print("鲲鹏志 · 书库索引 → Cloudflare Vectorize")
    print("=" * 50)

    # 检查索引状态
    info = await vectorize_info()
    if info:
        print(f"索引名: {info.get('name')}")
        print(f"维度: {info.get('config', {}).get('dimensions')}")
        print(f"度量: {info.get('config', {}).get('metric')}")
        print()

    retriever = BookRetriever()
    
    # 本地书库路径 - 假设在 ~/kunpengzhi
    book_root = os.path.join(os.path.expanduser("~"), "kunpengzhi")
    if not os.path.exists(book_root):
        print(f"❌ 错误: 本地书库未找到 -> {book_root}")
        print("请先将 kunpengzhi 仓库克隆到 ~/kunpengzhi/")
        sys.exit(1)

    # 模拟 retriever.get_content_path()
    # 强制本地路径
    BookRetriever.get_content_path = lambda: book_root

    all_chapters = {}

    # 牧人记
    book = "牧人记"
    book_path = os.path.join(book_root, book)
    if os.path.isdir(book_path):
        for ch in sorted(os.listdir(book_path)):
            if ch.endswith(".md"):
                ch_path = os.path.join(book_path, ch)
                with open(ch_path, "r") as f:
                    all_chapters[f"{book}/{ch}"] = f.read()
                    print(f"  📖 {book}/{ch} ({len(all_chapters[f'{book}/{ch}'])} chars)")

    # 双约记
    book = "双约记"
    book_path = os.path.join(book_root, book)
    if os.path.isdir(book_path):
        for ch in sorted(os.listdir(book_path)):
            if ch.endswith(".md"):
                ch_path = os.path.join(book_path, ch)
                with open(ch_path, "r") as f:
                    all_chapters[f"{book}/{ch}"] = f.read()
                    print(f"  📖 {book}/{ch} ({len(all_chapters[f'{book}/{ch}'])} chars)")

    # 牧兰记
    book = "牧兰记"
    book_path = os.path.join(book_root, book)
    if os.path.isdir(book_path):
        for ch in sorted(os.listdir(book_path)):
            if ch.endswith(".md"):
                ch_path = os.path.join(book_path, ch)
                with open(ch_path, "r") as f:
                    all_chapters[f"{book}/{ch}"] = f.read()
                    print(f"  📖 {book}/{ch} ({len(all_chapters[f'{book}/{ch}'])} chars)")

    # 牧月记
    book = "牧月记"
    book_path = os.path.join(book_root, book)
    if os.path.isdir(book_path):
        for ch in sorted(os.listdir(book_path)):
            if ch.endswith(".md"):
                ch_path = os.path.join(book_path, ch)
                with open(ch_path, "r") as f:
                    all_chapters[f"{book}/{ch}"] = f.read()
                    print(f"  📖 {book}/{ch} ({len(all_chapters[f'{book}/{ch}'])} chars)")

    # 彩虹屁 + 批判
    digest_base = os.path.join(book_root, "digest")
    if os.path.isdir(digest_base):
        for dig_dir in ["彩虹屁", "批判"]:
            dig_path = os.path.join(digest_base, dig_dir)
            if os.path.isdir(dig_path):
                for fname in os.listdir(dig_path):
                    if fname.endswith(".md"):
                        fpath = os.path.join(dig_path, fname)
                        with open(fpath, "r") as f:
                            key = f"{dig_dir}/{fname}"
                            all_chapters[key] = f.read()
                            print(f"  📝 {key} ({len(all_chapters[key])} chars)")

    print(f"\n共 {len(all_chapters)} 个文件, 开始索引...")
    total = await index_sources(all_chapters)
    print(f"\n✅ 索引完成: {total} chunks 已写入 Cloudflare Vectorize")


if __name__ == "__main__":
    asyncio.run(main())
