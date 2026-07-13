#!/usr/bin/env python3
import sys, os, json, uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from core.embeddings import VoyageEmbeddings
from core.search import graph_rag_search

app = FastAPI(title="mem-ops API", version="0.1.0")
embeddings = VoyageEmbeddings()

class MemoryInput(BaseModel):
    agent: str
    content: str
    title: Optional[str] = ""

class MemoryOutput(BaseModel):
    agent: str
    trimmed: str
    entities: list = []

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/api/trim", response_model=MemoryOutput)
def trim_memory(mem: MemoryInput):
    if not mem.content.strip():
        raise HTTPException(400, "empty content")
    result = graph_rag_search(mem.content, top_k=3)
    trimmed = result.get("answer", mem.content) if isinstance(result, dict) else mem.content
    return MemoryOutput(agent=mem.agent, trimmed=trimmed, entities=result.get("entities", []))

if __name__ == "__main__":
    port = int(os.getenv("MEM_OPS_PORT", "8800"))
    uvicorn.run(app, host="0.0.0.0", port=port)
