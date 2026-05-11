import asyncio
import os
from dotenv import load_dotenv
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_ext.models.openai import OpenAIChatCompletionClient
from autogen_agentchat.ui import Console
from core.config import config

# Ensure .env is loaded
load_dotenv()

async def test_chapter_debate():
    chapter_path = "/home/ben/kunpengzhi/牧人记/第07章 木兰无长兄.md"
    print(f"🚀 Loading Chapter: {chapter_path}")
    
    if not os.path.exists(chapter_path):
        print(f"❌ Error: File not found at {chapter_path}")
        return

    with open(chapter_path, 'r', encoding='utf-8') as f:
        context = f.read()

    print(f"✅ Context loaded ({len(context)} characters)")
    print(f"🤖 Using Model: {config.DEBATE_MODEL}")
    print(f"🌐 Using Base URL: {config.OPENAI_BASE_URL}")
    
    # Modern AutoGen 0.4+ Model Client
    model_client = OpenAIChatCompletionClient(
        model=config.DEBATE_MODEL,
        api_key=config.OPENAI_API_KEY,
        base_url=config.OPENAI_BASE_URL,
    )

    topic = "木兰无长兄：北魏时期的兵役制度与民族融合"
    
    # Modern Assistant Agents
    pro_agent = AssistantAgent(
        name="Pro_Expert",
        model_client=model_client,
        system_message=f"你是鲲鹏志知识库的正方专家。基于以下《牧人记》章节内容，支持关于‘{topic}’的深度分析。重点讨论稀疏矩阵与赋税逻辑。请简明扼要。\n内容：{context[:5000]}",
    )

    con_agent = AssistantAgent(
        name="Con_Expert",
        model_client=model_client,
        system_message=f"你是鲲鹏志知识库的反方专家。基于以下《牧人记》章节内容，对‘{topic}’中的论点提出质疑或补充不同视角。重点寻找逻辑漏洞。请简明扼要。\n内容：{context[:5000]}",
    )

    # Use a Team to manage the debate
    team = RoundRobinGroupChat([pro_agent, con_agent], max_turns=4)

    print("\n--- 🎤 辩论开始 (Modern AutoGen 1.0 Demo) ---\n")
    
    # Use Console UI to stream the debate
    await Console(team.run_stream(task=f"开始针对‘{topic}’进行深度对谈。正方先发。"))

if __name__ == "__main__":
    asyncio.run(test_chapter_debate())
