import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Database Configuration
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_PORT = int(os.getenv("DB_PORT", "3306"))
    DB_USER = os.getenv("DB_USER", "root")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "")
    DB_NAME = os.getenv("DB_NAME", "river")
    
    # OpenAI Configuration
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
    OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    DEBATE_MODEL = os.getenv("DEBATE_MODEL", "gemini-2.5-flash")
    
    # Voyage AI for Embeddings
    VOYAGE_API_KEY = os.getenv("VOYAGE_API_KEY", "")
    VOYAGE_API_URL = os.getenv("VOYAGE_API_URL", "https://api.voyageai.com/v1/embeddings")
    VOYAGE_MODEL = os.getenv("VOYAGE_MODEL", "voyage-large-2")
    
    # GraphRAG Configuration
    POLL_INTERVAL = int(os.getenv("POLL_INTERVAL", "60"))
    
    # Wiki.js Configuration
    WIKI_JS_URL = os.getenv("WIKI_JS_URL", "https://wiki.seekkey.eu.org/graphql")
    WIKI_JS_TOKEN = os.getenv("WIKI_JS_TOKEN", "")
    
    # Chainlit Configuration
    CHAINLIT_AUTH_SECRET = os.getenv("CHAINLIT_AUTH_SECRET", "")
    APP_PASSWORD = os.getenv("APP_PASSWORD", "3131")
    
    # Path Configuration
    CHAPTER_DIR = os.getenv("CHAPTER_DIR", "./.files/chapters/")

config = Config()
