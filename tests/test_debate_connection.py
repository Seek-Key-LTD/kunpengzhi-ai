import autogen
import asyncio
from core.config import config
from core.search import graph_rag_search

async def test_1v1_debate():
    print(f"Testing 1v1 Debate with LiteLLM: {config.OPENAI_BASE_URL}")
    
    llm_config = {
        "config_list": [
            {
                "model": config.DEBATE_MODEL,
                "api_key": config.OPENAI_API_KEY,
                "base_url": config.OPENAI_BASE_URL
            }
        ]
    }

    topic = "雅尔塔体系是否加速了冷战爆发？"
    
    pro_agent = autogen.AssistantAgent(
        name="Pro_Debater",
        system_message=f"You support the idea: {topic}. Be concise.",
        llm_config=llm_config,
    )

    con_agent = autogen.AssistantAgent(
        name="Con_Debater",
        system_message=f"You oppose the idea: {topic}. Be concise.",
        llm_config=llm_config,
    )

    # 1v1 conversation
    await pro_agent.a_initiate_chat(
        con_agent,
        message=f"Let's debate: {topic}. I'll start first.",
        max_turns=2
    )

if __name__ == "__main__":
    asyncio.run(test_1v1_debate())
