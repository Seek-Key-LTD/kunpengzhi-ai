import chainlit as cl
import asyncio
import os
from debate.modern_engine import ModernDebateEngine
from core.config import config
from core.search import get_global_mapping

@cl.on_chat_start
async def start():
    """Initialize the Modern Kunpengzhi AI Debate System (v1.1)."""
    chapter_dir = "/home/ben/kunpengzhi/牧人记/"
    chapters = []
    if os.path.exists(chapter_dir):
        chapters = [f.replace(".md", "") for f in os.listdir(chapter_dir) if f.endswith(".md")]
        chapters.sort()

    # Fixed cl.Action for Chainlit 1.3+ Compatibility
    actions = []
    for c in chapters[:8]:
        # Using payload as required by newer Pydantic/Chainlit versions
        actions.append(cl.Action(
            name="select_chapter", 
            value=c, 
            label=c[:12] + "..",
            payload={"value": c} 
        ))
    
    await cl.Message(
        content=f"""🦅 **鲲鹏志 1.1: 全景 GraphRAG 辩论系统**

系统已就绪，已连接 OCI HeatWave 核心。
请直接点击按钮开始，或输入编号。
""",
        actions=actions
    ).send()

@cl.action_callback("select_chapter")
async def on_action(action: cl.Action):
    # Retrieve value from payload to be safe
    topic_value = action.payload.get("value", action.value)
    await main(cl.Message(content=topic_value))

@cl.on_message
async def main(message: cl.Message):
    """Handle debate requests with Global Mapping and Provocative 1v1."""
    topic = message.content.strip()
    
    # 1. Human-Centric Global Mapping
    status_msg = cl.Message(content=f"📡 **正在调取 40 万字全景地图...**")
    await status_msg.send()
    
    global_map = get_global_mapping(topic)
    await cl.Message(content=global_map).send()

    # 2. Local Context Search
    chapter_dir = "/home/ben/kunpengzhi/牧人记/"
    chapter_context = None
    matched_file = None
    
    if os.path.exists(chapter_dir):
        files = os.listdir(chapter_dir)
        for f in files:
            if not f.endswith(".md"): continue
            if topic in f or topic.zfill(2) in f:
                matched_file = f
                break

    if matched_file:
        chapter_path = os.path.join(chapter_dir, matched_file)
        await cl.Message(content=f"📖 **加载本地原文**: `{matched_file}`").send()
        with open(chapter_path, 'r', encoding='utf-8') as f:
            chapter_context = f.read()
        await cl.Message(content=f"📜 **预览**:\n---\n{chapter_context[:800]}...\n---").send()
    else:
        await cl.Message(content=f"🔍 未发现本地匹配，将使用 HeatWave 全量搜索。").send()

    try:
        # 3. Engine Init
        engine = ModernDebateEngine(topic, chapter_context=chapter_context)
        team = engine.create_debate_team(num_pro=1, num_con=1)

        await cl.Message(content=f"🎬 **辩论开始 (1v1 + Coordinator)**").send()

        # 4. Token Streaming
        async def run_and_display():
            current_author = None
            current_msg = None

            async for event in team.run_stream(task=f"开始针对‘{topic}’进行深度辩论。"):
                source = getattr(event, 'source', None)
                content = getattr(event, 'content', None)

                if content:
                    if source != current_author:
                        current_author = source
                        current_msg = cl.Message(author=source, content="")
                        await current_msg.send()
                    
                    # Smooth streaming
                    chunk_size = 6
                    for i in range(0, len(content), chunk_size):
                        chunk = content[i:i+chunk_size]
                        await current_msg.stream_token(chunk)
                        await asyncio.sleep(0.01)
                    
                    await current_msg.update()

        await run_and_display()
        await cl.Message(content="🏆 **当前回合结束**。").send()

    except Exception as e:
        await cl.Message(content=f"❌ 运行错误: {str(e)}").send()
