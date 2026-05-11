import chainlit as cl
from autogen import AssistantAgent
import os
import requests

# 配置
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
WIKI_JS_URL = os.getenv("WIKI_JS_URL", "https://wiki.git4ta.fun")
WIKI_JS_TOKEN = os.getenv("WIKI_JS_TOKEN")

@cl.on_chat_start
async def start():
    """初始化辩论系统"""
    await cl.Message(
        content="""🦅 **鲲鹏志 4v4 辩论系统**

我可以组织 4v4 辩论队，辩题包括：
- 历史事件分析
- 地缘政治博弈  
- 文明演进路径
- 技术发展趋势

请输入您想辩论的议题，例如：
"雅尔塔体系是否加速了冷战爆发？"
"""
    ).send()

@cl.on_message
async def main(message: cl.Message):
    """处理辩论请求"""
    topic = message.content
    
    msg = cl.Message(content=f"🎯 **辩题**: {topic}\n\n正在从 Wiki.js 获取相关知识...")
    await msg.send()
    
    try:
        # 从 Wiki.js 获取相关内容
        wiki_content = fetch_wiki_content(topic)
        
        # 创建 8 个智能体（4v4）
        agents = create_debate_agents(topic, wiki_content)
        
        # 启动辩论
        debate_result = await run_debate(agents, topic)
        
        await msg.stream_token(f"\n\n✅ **辩论完成**\n\n{debate_result}")
        
    except Exception as e:
        await cl.Message(
            content=f"❌ 辩论出错：{str(e)}"
        ).send()

def fetch_wiki_content(topic):
    """从 Wiki.js GraphQL API 获取内容"""
    if not WIKI_JS_TOKEN:
        return "Wiki.js 未配置，使用默认知识"
    
    query = f"""
    {{
      pages {{
        list(query: "{topic}") {{
          title
          description
          path
        }}
      }}
    }}
    """
    
    try:
        response = requests.post(
            f"{WIKI_JS_URL}/api/graphql",
            json={"query": query},
            headers={"Authorization": f"Bearer {WIKI_JS_TOKEN}"}
        )
        data = response.json()
        pages = data.get('data', {}).get('pages', {}).get('list', [])
        return f"找到 {len(pages)} 个相关页面"
    except Exception as e:
        return f"Wiki.js 查询失败: {str(e)}"

def create_debate_agents(topic, context):
    """创建 4v4 辩论智能体"""
    
    # 正方 4 人
    pro_agents = [
        AssistantAgent(
            name=f"正方_{i}",
            llm_config={"config_list": [{"model": "gpt-4", "api_key": OPENAI_API_KEY}]},
            system_message=f"""你是鲲鹏志知识库的正方辩手 #{i}。
辩题：{topic}
你的立场：支持该观点
背景知识：{context}
要求：引用历史事实、数据支撑、逻辑严密"""
        )
        for i in range(1, 5)
    ]
    
    # 反方 4 人
    con_agents = [
        AssistantAgent(
            name=f"反方_{i}",
            llm_config={"config_list": [{"model": "gpt-4", "api_key": OPENAI_API_KEY}]},
            system_message=f"""你是鲲鹏志知识库的反方辩手 #{i}。
辩题：{topic}
你的立场：反对该观点
背景知识：{context}
要求：提出质疑、指出漏洞、提供反例"""
        )
        for i in range(1, 5)
    ]
    
    return pro_agents + con_agents

async def run_debate(agents, topic):
    """运行辩论流程"""
    results = []
    
    # 简化版：轮流发言
    for agent in agents[:4]:
        response = f"**{agent.name}**: 我认为{topic}是正确的，因为..."
        results.append(response)
    
    for agent in agents[4:]:
        response = f"**{agent.name}**: 我不同意，理由是..."
        results.append(response)
    
    return "\n\n".join(results)
