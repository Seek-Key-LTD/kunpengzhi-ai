import autogen
from typing import List, Dict
from core.config import config
from core.search import graph_rag_search

class DebateEngine:
    def __init__(self, topic: str):
        self.topic = topic
        self.llm_config = {
            "config_list": [
                {
                    "model": config.DEBATE_MODEL, 
                    "api_key": config.OPENAI_API_KEY,
                    "base_url": config.OPENAI_BASE_URL
                }
            ],
            "cache_seed": 42,
        }
        self.knowledge_context = self._get_knowledge_context()

    def _get_knowledge_context(self) -> str:
        """Fetch relevant knowledge using GraphRAG."""
        results = graph_rag_search(self.topic, top_k=3)
        context = "Relevant Knowledge from Kunpengzhi Knowledge Base:\n"
        
        # Vector results
        for res in results.get('vector_results', []):
            context += f"- {res['content']}\n"
            
        # Graph results
        if results.get('graph_results'):
            context += "\nRelated Entities and Relations:\n"
            for rel in results['graph_results']:
                context += f"- {rel['source_entity']} {rel['relation_type']} {rel['target_entity']}\n"
        
        return context

    def create_agents(self):
        # 1. Moderator
        moderator = autogen.AssistantAgent(
            name="Moderator",
            system_message=f"You are the moderator of the Kunpengzhi AI Debate. The topic is: {self.topic}. "
                           "Your job is to introduce the topic, manage the flow of 4v4 debate, and provide a final summary. "
                           "Keep the debate professional and intellectually stimulating.",
            llm_config=self.llm_config,
        )

        # 2. Pro-team (4 members)
        pro_agents = []
        for i in range(1, 5):
            agent = autogen.AssistantAgent(
                name=f"Pro_Debater_{i}",
                system_message=f"You are member #{i} of the PRO team. The topic is: {self.topic}. "
                               "Your position: STRONGLY SUPPORT. "
                               f"Knowledge base context: {self.knowledge_context}. "
                               "Use historical facts and logical reasoning. Be concise but impactful.",
                llm_config=self.llm_config,
            )
            pro_agents.append(agent)

        # 3. Con-team (4 members)
        con_agents = []
        for i in range(1, 5):
            agent = autogen.AssistantAgent(
                name=f"Con_Debater_{i}",
                system_message=f"You are member #{i} of the CON team. The topic is: {self.topic}. "
                               "Your position: STRONGLY OPPOSE. "
                               f"Knowledge base context: {self.knowledge_context}. "
                               "Identify flaws in the Pro team's logic and provide counter-examples.",
                llm_config=self.llm_config,
            )
            con_agents.append(agent)

        return moderator, pro_agents, con_agents

    async def run_debate_with_chainlit(self):
        """Run the debate and stream messages directly to Chainlit."""
        import chainlit as cl
        moderator, pro_agents, con_agents = self.create_agents()
        all_agents = [moderator] + pro_agents + con_agents
        
        groupchat = autogen.GroupChat(
            agents=all_agents,
            messages=[],
            max_round=12,
            speaker_selection_method="round_robin",
        )
        
        manager = autogen.GroupChatManager(groupchat=groupchat, llm_config=self.llm_config)

        # Intercept messages for Chainlit
        def chainlit_reply(recipient, messages, sender, config):
            last_message = messages[-1]
            content = last_message.get("content", "")
            if content:
                # We need to run this in the Chainlit loop
                asyncio.create_task(cl.Message(
                    author=sender.name,
                    content=content
                ).send())
            return False, None # Continue to next replier

        # Register interception on the manager for each agent's message
        for agent in all_agents:
            manager.register_reply(
                [autogen.Agent, None],
                reply_func=chainlit_reply,
                config=None,
            )

        # Start the chat
        # The moderator will start the conversation in the group chat managed by 'manager'
        await moderator.a_initiate_chat(
            manager,
            message=f"Debate begins: {self.topic}. Moderator, please start the session by introducing the topic and inviting Pro_Debater_1."
        )

import asyncio
