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
    OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    
    # Voyage AI for Embeddings
    VOYAGE_API_KEY = os.getenv("VOYAGE_API_KEY", "")
    
    # Wiki.js Configuration
    WIKI_JS_URL = os.getenv("WIKI_JS_URL", "https://wiki.seekkey.eu.org/graphql")
    WIKI_JS_TOKEN = os.getenv("WIKI_JS_TOKEN", "")
    
    # Chainlit Configuration
    CHAINLIT_AUTH_SECRET = os.getenv("CHAINLIT_AUTH_SECRET", "")

config = Config()
