# System Architecture
# AI Dev Evaluator v2 + myRAG

---

## High-Level Component Map

```
┌─────────────────────────────────────────────────────────────────────────┐
│  Browser (React + TypeScript + Zustand)                                  │
│                                                                          │
│  ┌──────────────────────┐   ┌────────────────────────────────────────┐  │
│  │  LEFT SIDE           │   │  RIGHT SIDE                            │  │
│  │  Context Layers      │   │  Evaluation & Suggestion               │  │
│  │                      │   │                                        │  │
│  │  [Mock | Actual Data]│   │  PRD Section                           │  │
│  │  system   ▓▓▓▓▓▓▓▓  │   │  ┌─────────────────┐                  │  │
│  │  user     ▓▓▓▓▓▓▓▓  │   │  │ Upload / Paste  │                  │  │
│  │  history  ▓▓▓▓▓▓▓▓  │   │  │ [Process PRD]   │→ myRAG           │  │
│  │  knowledge▓▓▓▓▓▓▓▓  │   │  └─────────────────┘                  │  │
│  │  tools    ▓▓▓▓▓▓▓▓  │   │                                        │  │
│  │  state    ▓▓▓▓▓▓▓▓  │   │  Evaluation Parameters (editable)      │  │
│  │                      │   │                                        │  │
│  │  Token budget bar    │   │  User Input ──────────────────────────┤  │
│  │                      │   │                                        │  │
│  │  [Assemble] [Run]    │   │  Model Response (from left + LLM)     │  │
│  │                      │   │                                        │  │
│  │  Configure LLM       │   │  Score Breakdown (hover→insight)      │  │
│  └──────────────────────┘   └────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘
         │                                   │
         │ HTTP                              │ HTTP
         ▼                                   ▼
┌─────────────────────────────┐   ┌─────────────────────────────┐
│  ai-dev-evaluator backend   │   │  myRAG service              │
│  FastAPI  :8000             │   │  FastAPI  :8001             │
│                             │   │                             │
│  /api/v1/workbench/*        │   │  /api/v1/documents/*        │
│  /api/v1/config/llm         │   │  /api/v1/queries/ask        │
│  /api/v1/config/actual-data │   │  /api/v1/health             │
│  /api/v1/prd/*              │   │                             │
│  /api/v1/evaluate/*         │   │  Ingestion pipeline         │
│                             │   │  Hybrid retrieval           │
│  PostgreSQL (eval DB)       │   │  Bounded ReAct loop         │
└─────────────────────────────┘   │                             │
                                  │  PostgreSQL + pgvector      │
                                  └─────────────────────────────┘
```

---

## Data Flow — Test Run (Actual Data mode)

```
User Input entered
       │
       ▼
[1] Fetch Actual Data APIs (parallel)
    ├─ system_prompt API → system layer content
    ├─ conversation_history API → history layer content (summarize if >5)
    ├─ knowledge API → knowledge layer content
    ├─ tools API → tools layer content
    └─ state API → state layer content

       │
       ▼
[2] Assemble prompt (ai-dev-evaluator backend)
    → concatenate enabled layers in order
    → calculate token counts

       │
       ▼
[3] Call configured LLM (ai-dev-evaluator backend)
    → provider: OpenAI / Anthropic / Gemini / Custom
    → return Model Response

       │
       ▼
[4] Evaluation Agent (ai-dev-evaluator backend)
    │
    ├─ [4a] Build evaluation context
    │   ├─ Query myRAG with user input → PRD evidence + citations
    │   ├─ Get conversation history (from Actual Data or local, last 5 summarized)
    │   ├─ Get tools (from Actual Data)
    │   ├─ Get state (from Actual Data)
    │   └─ Generate eval system prompt from PRD evidence
    │
    ├─ [4b] Generate reference response
    │   └─ Call LLM with eval context → reference answer (not shown in UI)
    │
    └─ [4c] Score Model Response
        ├─ For each evaluation parameter:
        │   Compare Model Response vs reference response + PRD evidence
        │   Score 0-5 with reasoning
        └─ Return: quality_score, score_breakdown, insights

       │
       ▼
[5] Display
    ├─ Model Response (text)
    ├─ Score bars (hover → insight per dimension)
    └─ Persist to run history (PostgreSQL)
```

---

## Data Flow — PRD Processing

```
User uploads PDF / pastes text
       │
       ▼
[1] ai-dev-evaluator backend
    → POST /api/v1/prd/upload
    → forward to myRAG POST /api/v1/documents/upload
    → store document_id

       │
       ▼
[2] myRAG ingestion pipeline
    → parse document
    → detect mode (structured / unstructured / scanned)
    → chunk + extract structure
    → generate embeddings
    → build retrieval graph
    → persist to PostgreSQL + pgvector

       │
       ▼
[3] Extract evaluation parameters
    → POST /api/v1/queries/ask (multiple queries):
      "What is the expected persona and tone?"
      "What policies or rules must the AI follow?"
      "What are the key user needs this system must address?"
      "What quality dimensions should responses be evaluated on?"
    → LLM synthesizes answers → derive evaluation parameters with descriptions
    → Return structured parameter list

       │
       ▼
[4] Frontend displays editable parameter list
    → User reviews, edits, saves
    → Stored in ai-dev-evaluator PostgreSQL
```

---

## myRAG Internal Architecture

```
POST /api/v1/documents/upload
       │
       ▼
ingest_service.py
  ├─ parser_service.py       → extract text, pages, raw structure
  ├─ mode_detector.py        → classify: structured/semi/unstructured/scanned
  ├─ structure_extractor.py  → headings, sections, tables, references
  ├─ chunk_service.py        → mode-appropriate chunking strategy
  ├─ summary_service.py      → page + section summaries via LLM
  ├─ embedding_service.py    → embed chunks via configured provider
  └─ graph_builder.py        → build TreeGraph / ChunkGraph / PageGraph
         │
         ▼
    PostgreSQL + pgvector


POST /api/v1/queries/ask
       │
       ▼
query_classifier.py    → classify query type
       │
       ▼
hybrid_retriever.py
  ├─ lexical_retriever.py    → BM25 / pg full-text
  ├─ semantic_retriever.py   → pgvector top-k
  └─ structure_retriever.py  → section / heading match
       │
       ▼
reranker.py            → normalize + merge + score candidates
       │
       ▼
sufficiency_checker.py
  ├─ sufficient? → answer_generator.py → response with citations
  └─ insufficient? → react_loop.py (bounded)
         ├─ state.py          working memory + step counter
         ├─ actions.py        10 allowed retrieval actions
         ├─ stop_conditions.py
         └─ decision_trace.py compact reasoning summary
               │
               ▼
         answer_generator.py → grounded response with citations
```

---

## ai-dev-evaluator Backend — New Modules (Phase 2)

```
backend/app/
├── api/
│   ├── config.py          # POST /config/llm, /config/actual-data
│   ├── prd.py             # POST /prd/upload, POST /prd/process
│   └── evaluate.py        # POST /evaluate/run
├── services/
│   ├── llm_client.py      # Call configured LLM (OpenAI/Anthropic/Gemini)
│   ├── actual_data.py     # Fetch from user-configured APIs
│   ├── eval_agent.py      # Evaluation context assembly + scoring (from scratch)
│   └── myrag_client.py    # HTTP client for myRAG service
├── models/
│   ├── config.py          # LLMConfig, ActualDataConfig ORM models
│   ├── prd.py             # PRDDocument ORM model
│   └── eval_param.py      # EvaluationParameter ORM model
└── schemas/
    ├── config.py          # LLMConfigSchema, ActualDataConfigSchema
    ├── prd.py             # PRDUploadResponse, EvalParameterSchema
    └── evaluate.py        # EvaluateRequest/Response, InsightSchema
```

---

## Database Layout

### ai-dev-evaluator DB (PostgreSQL)

| Table | Purpose |
|-------|---------|
| `llm_configs` | Provider, model, encrypted API key, temperature, max_tokens |
| `actual_data_configs` | Layer slot, URL, method, headers, body template, json_path |
| `prd_documents` | myRAG document_id, filename, uploaded_at |
| `eval_parameters` | Name, description, weight, prd_document_id |
| `run_history` | Replaces in-memory store from Phase 1 |
| `conversation_history` | Local store for multi-turn simulation |

### myRAG DB (PostgreSQL + pgvector)

| Table | Purpose |
|-------|---------|
| `documents` | File metadata, mode, status, checksum |
| `pages` | Raw text, summary, layout_type, ocr_confidence |
| `chunks` | Text, embedding vector, section_title, prev/next links |
| `graph_nodes` | node_type, title, summary, page range |
| `graph_edges` | from/to node, edge_type, weight |
| `query_logs` | Query text, type, agent used, retrieval trace |
| `answer_logs` | Answer text, confidence, citations |

---

## Security Considerations

- LLM API keys: encrypt at rest (Fernet symmetric encryption, key from env)
- Actual Data API secrets: same encryption
- myRAG file uploads: validate MIME type + size cap (configurable)
- myRAG path confinement: all file reads confined to upload dir
- No raw chain-of-thought leaked — only structured reasoning summaries stored
- User-configured API calls: proxy through backend, not browser (avoids CORS + key exposure)
- PostgreSQL credentials: env vars only, never in source
