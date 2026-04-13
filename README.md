# Context Engineering Playground

A full-stack evaluation platform that lets you simulate prompt assembly by enabling/disabling context layers, then shows the assembled prompt, token budget, model result, quality score, and run history.

---

## Quick Start

### Backend

```bash
cd backend
pip install -r requirements.txt
cp .env.example .env
uvicorn main:app --reload
```

API runs at: http://localhost:8000
Interactive docs: http://localhost:8000/docs

### Frontend

```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```

App runs at: http://localhost:5173

---

## Environment Variables

### Frontend (`frontend/.env`)

| Variable | Default | Description |
|----------|---------|-------------|
| `VITE_API_BASE_URL` | `http://localhost:8000` | Backend API base URL |

### Backend (`backend/.env`)

| Variable | Default | Description |
|----------|---------|-------------|
| `APP_ENV` | `development` | Environment name |
| `APP_HOST` | `0.0.0.0` | Host to bind |
| `APP_PORT` | `8000` | Port to listen on |
| `CORS_ORIGINS` | `http://localhost:5173,...` | Allowed CORS origins (comma-separated) |

---

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health check |
| GET | `/api/v1/workbench/defaults` | Load default layers + seeded history |
| POST | `/api/v1/workbench/assemble` | Assemble enabled layers into prompt |
| POST | `/api/v1/workbench/run` | Run evaluation and get scored result |
| GET | `/api/v1/workbench/runs` | List all run history |
| GET | `/api/v1/workbench/runs/{id}` | Get specific run result |
| POST | `/api/v1/workbench/reset-demo` | Reset to seeded state |

---

## How Mock Scoring Works

Scoring is implemented in `backend/app/services/evaluator.py`. It is deterministic and rule-based — no real LLM is called.

### Eight Dimensions (each scored 0–5)

| Dimension | Boosts |
|-----------|--------|
| `persona_adherence` | +3 if system, +1 if state |
| `policy_accuracy` | +3 if knowledge, +1 if system |
| `empathy_tone` | +2 if system, +1 if history |
| `context_awareness` | +2 if history, +1 if state, +1 if knowledge |
| `actionability` | +3 if tools, +1 if knowledge |
| `personalization` | +3 if state, +1 if system |
| `no_hallucination` | +2 if knowledge, +1 if tools |
| `completeness` | +1 per 2 active layers (max +4) |

All dimensions start at 1 and are capped at 5.
`quality_score` = sum of all 8 dimensions (max 40).

### Mock LLM Response

Responses in `backend/app/services/provider.py` are template-driven based on which layers are active:

- **Only user**: Generic unhelpful response with no persona or policy
- **+ system**: Empathetic intro, agent persona, no specific policy
- **+ knowledge**: Cites 45-day return window, portal bug INC-2024-1147, $15 credit
- **+ tools**: Adds specific action steps (lookup_order, process_replacement, issue_service_credit)
- **+ history**: References prior session, order #NT-2024-88341
- **+ state**: Uses customer name (Marcus), references Platinum tier

---

## Seeded Demo Data

Five pre-seeded runs demonstrate the progressive impact of adding context layers:

| Run | Active Layers | Score | Tokens |
|-----|--------------|-------|--------|
| 1 | user only | 9/40 | 45 |
| 2 | system + user | 17/40 | 168 |
| 3 | system + user + knowledge | 26/40 | 412 |
| 4 | system + user + knowledge + tools | 32/40 | 534 |
| 5 | all 6 layers | 38/40 | 847 |

---

## Where to Plug In Real APIs

### Real LLM

Replace `backend/app/services/provider.py`'s `generate_mock_response()` with a real provider call:

```python
# Example: OpenAI
from openai import AsyncOpenAI

async def generate_real_response(assembled_prompt: str) -> tuple[str, int]:
    client = AsyncOpenAI(api_key=settings.openai_api_key)
    start = time.monotonic()
    response = await client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": assembled_prompt}],
    )
    latency_ms = int((time.monotonic() - start) * 1000)
    return response.choices[0].message.content, latency_ms
```

### Real RAG (Knowledge Layer)

Replace the static `KNOWLEDGE_CONTENT` in `backend/app/data/seeds.py` with a retrieval call:

```python
async def retrieve_knowledge(user_query: str) -> str:
    # Call your vector DB (Pinecone, Weaviate, pgvector, etc.)
    results = await vector_db.search(user_query, top_k=5)
    return "\n\n".join(r.text for r in results)
```

### Real Tool Discovery (Tools Layer)

Replace static `TOOLS_CONTENT` with dynamic tool schema generation from your tool registry.

### Real CRM/State (State Layer)

Replace `STATE_CONTENT` with a live CRM lookup using the authenticated customer ID.

---

## Phase 2 Roadmap

- [ ] Real LLM provider integration (OpenAI, Anthropic, Gemini) with provider selector
- [ ] Real RAG pipeline — connect a vector database for dynamic knowledge retrieval
- [ ] Live token counting using provider-specific tokenizers (tiktoken, etc.)
- [ ] Side-by-side run comparison view
- [ ] Layer content version history and diff view
- [ ] Export runs as JSON or CSV
- [ ] Shareable run permalinks
- [ ] Custom scoring rubrics (user-defined dimensions and weights)
- [ ] Multi-turn conversation simulation
- [ ] Streaming LLM responses with live token display
- [ ] Authentication and multi-user support
- [ ] Persistent storage (PostgreSQL) replacing in-memory store
