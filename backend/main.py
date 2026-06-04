import os
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from openai import OpenAI
from articles import ARTICLES
from rag import build_chunks, VectorStore

load_dotenv()

app = FastAPI(title="TaskFlow Smart Escalation API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

_client = None

def get_client():
    global _client
    if _client is None:
        key = os.getenv("OPENAI_API_KEY")
        if not key:
            raise RuntimeError("OPENAI_API_KEY environment variable not set")
        _client = OpenAI(api_key=key)
    return _client

chunks = build_chunks(ARTICLES)
vector_store = VectorStore(chunks)

class QueryRequest(BaseModel):
    question: str

def escalate_unlikely(results):
    if any(r["score"] > 0.78 for r in results):
        return False
    avg = sum(r["score"] for r in results) / len(results)
    return avg < 0.72

def build_context(results):
    sections = []
    for r in results:
        sections.append(f"[Source: {r['title']} (relevance: {r['score']:.2f})]\n{r['text']}")
    return "\n\n".join(sections)

def classify_and_respond(question, context, results):
    avg_score = sum(r["score"] for r in results) / len(results)
    max_score = max(r["score"] for r in results)

    system_prompt = """You are a helpful support agent for TaskFlow, a project management SaaS.
Your job is to answer customer questions using ONLY the provided help article excerpts.
Follow these rules strictly:

1. If the context contains information relevant to the question, answer in a friendly, professional tone using only the provided context.
2. If any of these conditions apply, you MUST escalate instead of answering:
   - The question is completely off-topic (not about TaskFlow at all)
   - The context has no information relevant to the question
   - The context has only partial information and you cannot give a complete answer
   - The question asks about pricing details, account-specific data, or actions you cannot perform
   - The question is ambiguous and you cannot determine what the user is asking
3. When you escalate, politely explain that a human agent will follow up, and briefly state why.

Respond in this JSON format:
{"action": "answer"|"escalate", "response": "your message to the user", "confidence": "high"|"medium"|"low", "confidence_reason": "short explanation"}"""

    user_prompt = f"""Question from customer: {question}

Relevant help articles:
{context}

Retrieval confidence scores: avg={avg_score:.2f}, max={max_score:.2f}

Respond in the required JSON format."""

    resp = get_client().chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.2,
        response_format={"type": "json_object"},
    )

    import json
    return json.loads(resp.choices[0].message.content)

@app.post("/chat")
def chat(req: QueryRequest):
    results = vector_store.search(req.question, top_k=3)

    if escalate_unlikely(results):
        avg_score = sum(r["score"] for r in results) / len(results)
        return {
            "action": "escalate",
            "response": "I'm sorry, I couldn't find enough information in our help articles to answer your question accurately. A human agent will follow up with you shortly.",
            "confidence": "low",
            "confidence_reason": f"Retrieved content relevance too low (avg: {avg_score:.2f}). No matching help article found.",
            "results": results,
        }

    context = build_context(results)
    decision = classify_and_respond(req.question, context, results)
    decision["results"] = results

    if decision.get("action") == "escalate":
        if "confidence" not in decision:
            decision["confidence"] = "low"
        if "confidence_reason" not in decision:
            decision["confidence_reason"] = "LLM determined the question cannot be reliably answered from available help articles."

    return decision

@app.get("/health")
def health():
    return {"status": "ok"}

static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.isdir(static_dir):
    app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")
