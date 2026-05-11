from typing import List

def chunk_text(text: str, chunk_size: int = 500) -> List[str]:
    """Smartly split text into chunks based on paragraphs."""
    paragraphs = text.split('\n\n')
    chunks = []
    current_chunk = ""
    
    for para in paragraphs:
        if len(current_chunk) + len(para) < chunk_size:
            current_chunk += para + "\n\n"
        else:
            if current_chunk:
                chunks.append(current_chunk.strip())
            current_chunk = para + "\n\n"
    
    if current_chunk:
        chunks.append(current_chunk.strip())
    
    return chunks

def clean_content(text: str) -> str:
    """Basic text cleaning."""
    if not text:
        return ""
    # Add more cleaning logic as needed
    return text.strip()
