import requests
from typing import List
from .config import config

class VoyageEmbeddings:
    def __init__(self):
        self.api_key = config.VOYAGE_API_KEY
        self.model = config.VOYAGE_MODEL
        self.url = config.VOYAGE_API_URL

    def get_embedding(self, text: str) -> List[float]:
        """Generate embedding for a single text string."""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "input": [text[:8000]],  # Truncate to avoid API limits
            "model": self.model
        }
        
        response = requests.post(self.url, json=payload, headers=headers)
        response.raise_for_status()
        
        return response.json()["data"][0]["embedding"]

    def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for a list of text strings."""
        # Note: Voyage AI supports batching, but for simplicity we keep it linear 
        # or implement batching if needed for performance.
        return [self.get_embedding(t) for t in texts]
