import asyncio
import os
import json
from debate.modern_engine import ModernDebateEngine
from core.config import config
from core.search import get_global_mapping

async def test_modern_debate_cli(topic_input: str):
    """
    Robust CLI version of the 'Creative 1.0' system for tuning.
    Includes Global Mapping and Provocative 1v1.
    """
    print("="*80)
    print(f"🦅 Kunpengzhi AI Creative 1.0 - CLI Tuning Mode")
    print(f"Target Topic: {topic_input}")
    print("="*80)

    # 1. Global Mapping via OCI HeatWave
    print("\n📡 Fetching Global Panoramic Map from OCI HeatWave...")
    global_map = get_global_mapping(topic_input)
    print(f"\n{global_map}")

    # 2. Local Context Search
    chapter_dir = "/home/ben/kunpengzhi/牧人记/"
    chapter_context = None
    matched_file = None
    
    if os.path.exists(chapter_dir):
        files = os.listdir(chapter_dir)
        for f in files:
            if not f.endswith(".md"): continue
            if topic_input in f or topic_input.zfill(2) in f:
                matched_file = f
                break

    if matched_file:
        print(f"\n📖 Loaded Local Content: {matched_file}")
        with open(os.path.join(chapter_dir, matched_file), 'r', encoding='utf-8') as f:
            chapter_context = f.read()
        print(f"📜 Content Preview: {chapter_context[:200]}...")
    else:
        print("\n🔍 No local file match. System will rely solely on Global GraphRAG.")

    # 3. Initialize Engine
    print(f"\n🤖 Initializing Engine (Model: {config.DEBATE_MODEL})...")
    engine = ModernDebateEngine(topic_input, chapter_context=chapter_context)
    team = engine.create_debate_team(num_pro=1, num_con=1)

    # 4. Run Stream with Token Simulation
    print("\n" + "!"*80)
    print("🎬 DEBATE STARTING (Token Streaming Mode)")
    print("!"*80 + "\n")

    current_author = None
    async for event in team.run_stream(task=f"开始针对‘{topic_input}’进行深度辩论。"):
        source = getattr(event, 'source', None)
        content = getattr(event, 'content', None)

        if content:
            if source != current_author:
                print(f"\n\n--- 👤 {source} ---")
                current_author = source
            
            # Simulate real-time typing
            for char in content:
                print(char, end="", flush=True)
                await asyncio.sleep(0.005)

    print("\n\n" + "="*80)
    print("🏆 Debate Session Concluded.")
    print("="*80)

if __name__ == "__main__":
    import sys
    # Default to "01" if no argument provided
    topic = sys.argv[1] if len(sys.argv) > 1 else "01"
    asyncio.run(test_modern_debate_cli(topic))
