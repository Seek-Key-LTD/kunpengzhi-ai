import asyncio
import os
from typing import List, Optional
from dotenv import load_dotenv
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_ext.models.openai import OpenAIChatCompletionClient
from core.config import config
from core.search import graph_rag_search

class ModernDebateEngine:
    def __init__(self, topic: str, chapter_context: Optional[str] = None):
        self.topic = topic
        self.chapter_context = chapter_context or self._get_graphrag_context()
        self.model_client = OpenAIChatCompletionClient(
            model=config.DEBATE_MODEL,
            api_key=config.OPENAI_API_KEY,
            base_url=config.OPENAI_BASE_URL,
        )

    def _get_graphrag_context(self) -> str:
        """Fetch background knowledge and human-centric placement."""
        try:
            results = graph_rag_search(self.topic, top_k=5)
            
            # Extract arc/book info from path (e.g., /牧人记/第一卷/...)
            placement = "未知位置"
            if results.get('vector_results'):
                path = results['vector_results'][0].get('path', '')
                parts = [p for p in path.split('/') if p]
                if len(parts) >= 2:
                    placement = f"《{parts[0]}》· {parts[1]}"
            
            context_parts = [f"📍 **全景定位**: 本议题源自 **{placement}**，是 40 万字宏大叙事中的一个关键节点。"]
            
            # Add top relevant context
            if results.get('vector_results'):
                context_parts.append("\n🔍 **HeatWave 检索到的核心逻辑线**: ")
                for res in results['vector_results'][:2]:
                    context_parts.append(f"- {res['content'][:300]}...")
            
            return "\n".join(context_parts)
            
        except Exception as e:
            return f"⚠️ 全局定位暂不可用: {str(e)}"

    def create_debate_team(self, num_pro: int = 1, num_con: int = 1):
        # 1. Coordinator (Now focused on story placement and picking the "annoying" point)
        coordinator_instruction = f"""你是鲲鹏志实验室的首席协调官（握有权柄者）。
你的首要任务是：
1. 向大家介绍当前辩题在整部作品（40万字全景）中的位置和意义。不要说“第几章”，要说它属于哪个篇章或哪个逻辑模块。
2. 从以下背景资料中，挑选出一个最具有争议性、最“让人讨厌”的逻辑点：
---
{self.chapter_context}
---
3. 明确宣布本次辩论的“投名状”：
   - 正方 (Pro_Expert)：扮演“反叛者”，博斥 (博我) 这个点。
   - 反方 (Con_Expert)：扮演“卫道士”，捍卫 (战我) 这个点。
"""
        coordinator = AssistantAgent(
            name="Coordinator",
            model_client=self.model_client,
            system_message=coordinator_instruction,
        )

        # 2. Moderator (Flow manager)
        moderator = AssistantAgent(
            name="Moderator",
            model_client=self.model_client,
            system_message=f"你是主持人。在协调官抛出挑衅性命题后，先请正方（反叛者）开始博斥，再请反方（卫道士）进行捍卫。",
        )

        # 3. Pro-team (The Rebel/Attacker)
        pro_agents = []
        for i in range(1, num_pro + 1):
            agent = AssistantAgent(
                name=f"Pro_Expert",
                model_client=self.model_client,
                system_message=f"""你是正方专家（反叛者）。你的任务是：针对协调官点出的那个文本逻辑，进行全方位的博斥和质疑 (博我)。你要找出文本中的漏洞、傲慢或逻辑不通之处。

        【重要规则 - 信息来源透明度】
        1. 每次发言必须明确标注信息来源：
        - 如果引用 GraphRAG 向量检索结果，说明「根据 GraphRAG 向量检索到的《XXX》章节」
        - 如果引用知识图谱关系，说明「根据 GraphRAG 知识图谱中 {{entity_A}} → {{relation}} → {{entity_B}} 的关系」
        2. 不要编造不存在的来源
        3. 文本背景：{self.chapter_context[:2000]}...""",
            )
            pro_agents.append(agent)

        # 4. Con-team (The Defender)
        con_agents = []
        for i in range(1, num_con + 1):
            agent = AssistantAgent(
                name=f"Con_Expert",
                model_client=self.model_client,
                system_message=f"""你是反方专家（卫道士）。你的任务是：坚定地捍卫协调官点出的那个文本逻辑 (战我)。你要证明这个逻辑的深刻性和必要性，反击正方的质疑。

        【重要规则 - 信息来源透明度】
        1. 每次发言必须明确标注信息来源：
        - 如果引用 GraphRAG 向量检索结果，说明「根据 GraphRAG 向量检索到的《XXX》章节」
        - 如果引用知识图谱关系，说明「根据 GraphRAG 知识图谱中 {{entity_A}} → {{relation}} → {{entity_B}} 的关系」
        2. 不要编造不存在的来源
        3. 文本背景：{self.chapter_context[:2000]}...""",
            )
            con_agents.append(agent)

        participants = [coordinator, moderator]
        for p, c in zip(pro_agents, con_agents):
            participants.extend([p, c])
        
        return RoundRobinGroupChat(participants, max_turns=6)

    async def run_debate_stream(self, team, callback):
        """Run the debate and stream each message via callback."""
        async for message in team.run_stream(task=f"开始针对‘{self.topic}’进行深度辩论。"):
            # The message is a TaskResult or a message object
            # In autogen-agentchat, we can check for message types
            if hasattr(message, 'content'):
                callback(message.source, message.content)
            elif hasattr(message, 'messages') and message.messages:
                last_msg = message.messages[-1]
                callback(last_msg.source, last_msg.content)
