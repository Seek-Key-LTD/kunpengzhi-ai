#!/usr/bin/env python3
"""PDF 灌入 G-Brain 管线 — docs/gbrain-assets-flow.md §2 实现

用法:
  pdf_ingest.py <pdf> <slug> [--title T] [--source S] [--refs a,b,c] [--dry]

流程: ①宣告(建议先 mcp-registry assets put) ②pdftotext 提取 ③清洗 ④分块统计 ⑤gbrain put ⑥验证
"""
import argparse, re, subprocess, sys, os, json

GBRAIN = os.path.expanduser("~/.bun/bin/gbrain")


def extract(pdf):
    r = subprocess.run(["pdftotext", "-layout", pdf, "-"],
                       capture_output=True, text=True)
    if r.returncode != 0:
        raise SystemExit(f"pdftotext 失败: {r.stderr.strip()}")
    return r.stdout


def clean(text):
    """去页眉/页脚/页码/参考文献区/空行压缩（启发式，可按文档类型调参）"""
    lines = [l.strip() for l in text.split("\n")]
    out, skip = [], False
    for l in lines:
        if re.match(r"^(References|Bibliography|Literature Cited|参考文献|文献综述)\s*$", l):
            skip = True
        if skip:
            continue
        if re.match(r"^\d{1,4}\s*$", l):          # 孤立页码
            continue
        if re.match(r"^[A-Za-z &.'\-]{4,60}$", l) and not re.search(r"[\u4e00-\u9fff]", l):
            continue                              # 纯英文短行（页眉页脚）
        if re.search(r"Copyright|©|doi\.org|https?://", l) and len(l) < 80:
            continue                              # 版权/链接噪声
        out.append(l)
    return re.sub(r"\n{3,}", "\n\n", "\n".join(out)).strip()


def chunk_stats(text, size=800):
    """按语义块统计（供验证报告用；gbrain 入库时整篇 put，其内部自动分块嵌入）"""
    paras = [p.strip() for p in re.split(r"\n{2,}", text) if p.strip()]
    chunks, cur = [], ""
    for p in paras:
        if len(cur) + len(p) > size and cur:
            chunks.append(cur)
            cur = p
        else:
            cur = (cur + "\n\n" + p).strip()
    if cur:
        chunks.append(cur)
    return chunks


def gbrain_put(slug, md, title, source, refs):
    front = f"---\ntitle: \"{title}\"\nsource: \"{source}\"\nrefs: [{', '.join(f'\"{r}\"' for r in refs)}]\n---\n\n"
    r = subprocess.run(["bun", GBRAIN, "put", slug], input=front + md,
                       capture_output=True, text=True)
    if r.returncode != 0:
        raise SystemExit(f"gbrain put 失败: {r.stderr.strip()[-500:]}")
    return r.stdout


def gbrain_verify(slug):
    r = subprocess.run(["bun", GBRAIN, "get", slug], capture_output=True, text=True)
    if r.returncode != 0:
        return f"❌ get 失败: {r.stderr.strip()[-200:]}"
    return f"✅ 回读 {len(r.stdout)} 字符"


def main():
    ap = argparse.ArgumentParser(description="PDF → G-Brain 灌入管线")
    ap.add_argument("pdf")
    ap.add_argument("slug")
    ap.add_argument("--title", default="")
    ap.add_argument("--source", default="")
    ap.add_argument("--refs", default="")
    ap.add_argument("--dry", action="store_true", help="只提取+清洗+统计，不灌入")
    a = ap.parse_args()
    refs = [r for r in a.refs.split(",") if r]

    raw = extract(a.pdf)
    txt = clean(raw)
    chunks = chunk_stats(txt)
    print(f"① 提取 {len(raw)} 字符 → ② 清洗后 {len(txt)} 字符 → ③ 语义块 {len(chunks)} 块")

    if a.dry:
        print("🔍 dry-run：未灌入。块大小分布:", [len(c) for c in chunks[:5]], "...")
        return
    print("④ 灌入 gbrain:", a.slug)
    gbrain_put(a.slug, txt, a.title, a.source, refs)
    print("⑤ 验证:", gbrain_verify(a.slug))


if __name__ == "__main__":
    main()
