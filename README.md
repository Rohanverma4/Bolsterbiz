# TaskFlow Smart Escalation API

A full-stack AI-powered customer support agent for TaskFlow (a fictional project management SaaS), built with FastAPI + OpenAI + React.

## Live URL

(Deployed URL goes here)

## Setup Instructions

### Prerequisites
- Python 3.10+
- Node.js 18+

### Backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Create a `.env` file in `backend/`:
```
OPENAI_API_KEY=sk-your-key-here
```

Start the server:
```bash
uvicorn main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173 in your browser.

## Escalation Logic

The agent uses a two-stage escalation decision process:

**Stage 1 — Retrieval Confidence (pre-filter):** When a customer question comes in, we embed it and retrieve the top 3 most similar chunks from our help articles using cosine similarity. If no chunk scores above 0.78 and the average score is below 0.72, we immediately escalate. This catches completely off-topic questions (e.g., "What's the weather?") and questions about topics not covered by the help articles. The thresholds were chosen empirically: 0.78 represents a strong semantic match, and 0.72 as an average ensures that even if one chunk is borderline, we still give the LLM a chance.

**Stage 2 — LLM Judgement:** If retrieval passes Stage 1, we pass the retrieved context to GPT-4o-mini with a system prompt that instructs it to either answer (using only the provided context) or escalate. The LLM is instructed to escalate when: the question is off-topic for TaskFlow, the context has no relevant info, the context is only partial, the question requires account-specific data, or the question is ambiguous. The LLM returns a JSON response with an action, response text, confidence label, and reason.

This two-stage approach ensures we don't waste LLM calls on clearly unanswerable questions (Stage 1 acts as a cheap filter), while letting the LLM handle nuanced edge cases where the right action depends on understanding the question's intent.

## Trade-offs

- **In-memory vector store:** Using FAISS or an in-memory NumPy array is fine for 5 small articles. A production system would use pgvector, Pinecone, or Weaviate.
- **No chunk overlap tuning:** I used simple 300-word chunks with 50-word overlap. More sophisticated chunking (semantic splitting) would improve retrieval quality.
- **Fixed thresholds:** The 0.78/0.72 thresholds were chosen heuristically. In production, these should be tuned against a test set.
- **Single model call:** Stage 2 uses one LLM call for both classification and response generation. Separating classification from generation could improve reliability.

## What I'd Improve With More Time

1. **Test set & evaluation:** Build a labeled dataset of questions with expected actions (answer/escalate) and tune thresholds and prompts systematically.
2. **Better chunking:** Use semantic chunking (e.g., LangChain's recursive text splitter) or sentence-based splitting for more coherent context windows.
3. **Multi-turn conversation:** Track conversation history so follow-up questions can reference prior context.
4. **Confidence calibration:** Return numerical confidence scores from the LLM and calibrate them against actual accuracy.
5. **Streaming responses:** Stream the LLM response for a better UX.
6. **Caching:** Cache embeddings for frequent questions to reduce API costs.
7. **Logging & monitoring:** Log all Q&A pairs for analysis and continuous improvement.
