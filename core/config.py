import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    # OpenAI / LLM
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
    DEBATE_MODEL = os.getenv("DEBATE_MODEL", "gemini-2.5-flash")

    # Wiki.js
    WIKI_JS_URL = os.getenv("WIKI_JS_URL", "https://wiki.seekkey.eu.org/graphql")
    WIKI_JS_TOKEN = os.getenv("WIKI_JS_TOKEN", "")

    # Chainlit
    APP_PASSWORD = os.getenv("APP_PASSWORD", "3131")

    # TTS (微软免费语音)
    TTS_VOICE = os.getenv("TTS_VOICE", "zh-CN-YunxiNeural")
    TTS_ENABLED = os.getenv("TTS_ENABLED", "true").lower() == "true"

    # 路径
    CHAPTER_DIR = os.getenv("CHAPTER_DIR", "./.files/chapters/")


config = Config()
