import os
import numpy as np
from openai import OpenAI

_client = None

def get_client():
    global _client
    if _client is None:
        key = os.getenv("OPENAI_API_KEY")
        if not key:
            raise RuntimeError("OPENAI_API_KEY environment variable not set")
        _client = OpenAI(api_key=key)
    return _client

CHUNK_SIZE = 300
CHUNK_OVERLAP = 50

def chunk_article(title, content):
    words = content.split()
    chunks = []
    start = 0
    while start < len(words):
        end = min(start + CHUNK_SIZE, len(words))
        chunk_text = " ".join(words[start:end])
        chunks.append({"title": title, "text": chunk_text})
        start += CHUNK_SIZE - CHUNK_OVERLAP
    return chunks

def build_chunks(articles):
    all_chunks = []
    for article in articles:
        all_chunks.extend(chunk_article(article["title"], article["content"]))
    return all_chunks

def get_embedding(text):
    resp = get_client().embeddings.create(input=text, model="text-embedding-ada-002")
    return resp.data[0].embedding

class VectorStore:
    def __init__(self, chunks):
        self.chunks = chunks
        self.embeddings = np.array([get_embedding(c["text"]) for c in chunks])

    def search(self, query, top_k=3):
        q_emb = np.array(get_embedding(query))
        scores = np.dot(self.embeddings, q_emb) / (
            np.linalg.norm(self.embeddings, axis=1) * np.linalg.norm(q_emb)
        )
        top_indices = np.argsort(scores)[-top_k:][::-1]
        return [
            {
                "title": self.chunks[i]["title"],
                "text": self.chunks[i]["text"],
                "score": float(scores[i]),
            }
            for i in top_indices
        ]
