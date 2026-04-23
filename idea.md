# AI Dev Evaluator — Idea

## One-Line Pitch

A **context engineering playground** that makes prompt construction visible — toggle context layers on/off, see the assembled prompt, token budget, mock LLM response, and quality score, all in one UI.

## Problem

Prompt engineering is opaque. Developers building LLM-powered features don't have a fast way to:
- Understand which context layers (system prompt, RAG, tools, history, state) actually improve quality
- See the token cost of each layer
- Compare responses across different context combinations
- Demo the progressive impact of context to stakeholders

## Solution

A full-stack workbench where each context layer is a toggle:

```
[system] [user] [history] [knowledge] [tools] [state]
   ✓        ✓       ✗          ✓           ✗       ✗
                        ↓
              Assembled Prompt  →  Mock LLM  →  Score (26/40)
```

Six context layers, each independently enabled/disabled. Every combination produces a deterministic quality score across 8 dimensions (persona adherence, policy accuracy, empathy, context awareness, actionability, personalization, hallucination resistance, completeness).

## Context Layers

| Layer | Role |
|-------|------|
| `system` | Agent persona + tone instructions |
| `user` | The user's message (always required) |
| `history` | Prior conversation turns |
| `knowledge` | RAG-retrieved policy/knowledge content |
| `tools` | Available function/tool definitions |
| `state` | Live customer/session state (CRM data) |

## Scoring Model

8 dimensions × 5 points each = 40 max. Rules-based, deterministic, no LLM call needed for scoring. Each dimension maps to specific layer combinations (e.g. `tools` unlocks actionability, `knowledge` reduces hallucination).

## Demo Flow

Five seeded runs show the progression:
- Run 1 (user only): 9/40 — generic unhelpful response
- Run 2 (+system): 17/40 — persona appears
- Run 3 (+knowledge): 26/40 — policy-accurate
- Run 4 (+tools): 32/40 — actionable
- Run 5 (all 6): 38/40 — fully personalized

## Phase 2 Vision

Swap mock internals for real ones without changing the UI contract:
- Real LLM provider (OpenAI / Anthropic / Gemini) with provider selector
- Real RAG pipeline (vector DB — pgvector, Pinecone, Weaviate)
- Live token counting (tiktoken, Anthropic tokenizer)
- Side-by-side comparison, run export, custom scoring rubrics
- Multi-turn simulation, streaming responses
- Persistent storage (PostgreSQL) replacing in-memory store

## Tech Stack

| Layer | Choice | Reason |
|-------|--------|--------|
| Backend | FastAPI + Python 3.12 | Async, typed, OpenAPI auto-docs |
| Frontend | React 18 + TypeScript + Vite | Fast dev loop, typed |
| State | Zustand | Lightweight, no boilerplate |
| Storage | In-memory (Phase 1) → PostgreSQL (Phase 2) | Ship fast, upgrade cleanly |
| Scoring | Deterministic rules | No LLM cost, reproducible |

## Design Principles

- **No external API calls in Phase 1** — fully local, works offline
- **Mock → Real swap without UI changes** — service interfaces isolate the swap point
- **Seeded demo data** — product is instantly useful without setup
- **Local only** — no remote GitHub, no cloud deploy, no external services

## enhasment to existing application
 Allow user to upload the document by clicking + icon in header. This document once uploaded shall be  send to the    
  ingestion api which user has configured in RAG section available in “Actual Data” section , In “Actual Data” section 
   allow user to integrate 2 apis-> ingestion and search api. And output of search api shall be published in “retrieve 
   knowledge” text box. The user input shall be passed to search api to produce output.                                
  The uploaded document shall be available to myRAG as well for processing , so that the  “Result” which is actually a 
   Evaluation and suggestion side, can produce better response ,which it will use to compare the “model response” and  
  rate the “model response” using “evaluation parameter.”                                                              
  Make the “score” base be 100. And rate the “model response” on 100 base.                                             
                                                                                                                       
  Note  “Result” which is actually a Evaluation and suggestion side shall generate response (to compare it with “model 
   Response” and evaluate it.considering the “evaluation parameters”) using an agent, so create a lightweight          
  optimised agent from scratch, no langchain or langraph, this agent shall be specific to this task only and shall use 
   the  its own system prompt which it created based on PRD,store what shall be stored in  state & Memory , use myRAG, 
   conversation history ,tools(get these from actual data, sources are configured here) needed based on the user       
  input.                                                                                                               
                                                                                                                       
  myRAG shall get the DB details for PGvector or postgress from .env or the “Configure DB” section in Configure part   
  in header. And LLM details from “configure LLM” whichever LLM connection working successfully. 
  most of the above things are done , so dont redo, just verify and completed if anyone of them is not complete.
I want user to operate only from UI , not to ask him to set pgvector and env variables , so why shall we not write code in such a maner that user just need to configure LLM , DB there itself, I have already coded these things, please verify and fix if any bug you see
run this mode only when your database is PostgreSQL and the pgvector extension is enabled.

Typical setup is:

DB_PROVIDER=postgres
example DATABASE_URL=postgresql://USER:PASSWORD@HOST:5432/DBNAME

Then in PostgreSQL, enable pgvector in the same database your app uses:

CREATE EXTENSION IF NOT EXISTS vector;

That extension is installed per database, not globally for all databases.

A basic verification:

SELECT extname FROM pg_extension WHERE extname = 'vector';

Postgres keeps installed extensions in pg_extension.

A minimal table example:

CREATE TABLE documents (
  id bigserial PRIMARY KEY,
  content text,
  embedding vector(1536)
);

And a similarity search example:

SELECT id, content
FROM documents
ORDER BY embedding <-> '[0.1, 0.2, 0.3]'::vector
LIMIT 5;

pgvector supports storing embeddings in a vector(n) column and doing nearest-neighbor search in Postgres.

If you are configuring an app, the startup flow should usually be:

connect using DATABASE_URL
verify database is PostgreSQL
verify vector extension exists
run vector-table migrations
start the app

Pseudo-check:

# startup check
SELECT version();                     -- confirm postgres
SELECT extname FROM pg_extension
WHERE extname = 'vector';             -- confirm pgvector

## already implemented
I am trying to create a application where a user can configure his api and test the response get feedback  to improve.
Remember : if “ actual data ” is selected, “context layer” data need to be populated from apis configured in actual data , allow user to give system prompt by integrating api or by giving input in a textbox and saving it to be used as system prompt.

There are 2 sides here, “ Context Layer” that gets all its input from mock or “actual Data” where apis are configured by user.”Resut” Side ,this side also consumes apis configured in “Actual Data” section but need to have its own mechanism to process them.
 “Context Layer” side gets things from “actual Data” and LLM(which is configured in “cofigure LLM” section) shall process it produces “Model Response” and populate it with the outcome.
I want to create a myRAG which shall be working based on this :  
Build a production-oriented backend-only document processing and question-answering service in Python, with FastAPI APIs only. 
Very important constraints:
1. Do NOT use LangChain.
2. Do NOT use LangGraph.
3. Do NOT use any agent framework.
4. If agentic behavior is needed, implement it from scratch using a bounded ReAct-style loop in our own code.
5. Keep the code clean, modular, minimal, and easy to extend.
6. Prefer deterministic pipelines first, and only escalate to bounded agentic retrieval when initial evidence is insufficient.
7. Optimize for good answers on both structured and unstructured documents.
8. Every answer must be grounded in retrieved evidence and include citations.
9. Build only APIs, services, schemas, and internal processing modules.
10. Add a progress.md file and keep it updated with:
   - what feature was added
   - where it was added
   - what concept was used
   - any extra feature added
   - vulnerable areas and why

Goal:
Build a mode-adaptive document QA backend that processes uploaded documents and answers user queries using:
- hybrid retrieval
- structure-aware retrieval when possible
- bounded agentic sufficiency loop when needed
- no LangChain / LangGraph
- custom from-scratch orchestration

Core architecture:
The system must detect whether a document is:
- structured
- semi-structured
- unstructured
- scanned / layout-heavy

Then it should build the most appropriate internal retrieval graph:
- TreeGraph for structured docs
- ChunkGraph for unstructured docs
- PageGraph for scanned/layout-heavy docs

Use a common retrieval interface so all graph types can be queried consistently.

The design philosophy:
1. First pass should be deterministic and cheap:
   - lexical retrieval
   - embedding retrieval
   - metadata / structure retrieval
2. Then run a sufficiency check.
3. Only if evidence is insufficient, trigger a bounded ReAct-style retrieval loop.
4. The agent loop must be controlled, auditable, and limited by step count and token budget.
5. Final answers must only be generated from retrieved evidence.

Tech stack:
- Python 3.12+
- FastAPI
- Pydantic
- SQLAlchemy
- PostgreSQL
- pgvector
- Alembic
- PyMuPDF and/or pdfplumber for PDF parsing
- optional OCR integration placeholder for later
- BM25 or PostgreSQL full-text search for lexical retrieval
- embeddings via pluggable LLM provider adapter
- no frontend

Environment variables:
Create a .env.example with placeholders only. I will fill them later.
Include at minimum:
- APP_ENV=
- APP_HOST=
- APP_PORT=
- DATABASE_URL=
- VECTOR_DIMENSION=
- LLM_PROVIDER=
- LLM_MODEL=
- LLM_ACCESS_TOKEN=
- EMBEDDING_MODEL=
- EMBEDDING_ACCESS_TOKEN=
- OCR_PROVIDER=
- OCR_ACCESS_TOKEN=
- MAX_AGENT_STEPS=
- MAX_CONTEXT_TOKENS=
- DEFAULT_TOP_K=
- LOG_LEVEL=

High-level behavior:
A. Document ingestion:
- upload document
- store original file metadata
- parse document
- detect mode
- build chunks
- extract pages
- extract headings if possible
- extract tables if possible
- build summaries
- build references if possible
- create retrieval graph
- generate embeddings
- persist metadata, chunks, graph nodes, graph edges, and vectors

B. Query handling:
- classify query type
- perform first-pass hybrid retrieval
- rerank evidence
- run sufficiency check
- if sufficient: answer
- if insufficient: start bounded ReAct retrieval loop
- generate grounded response with citations and confidence

Document modes:
1. Structured mode:
   - detect headings, sections, subsections, appendices, notes, tables
   - build TreeGraph
   - preserve section hierarchy and page ranges
   - track cross-references

2. Unstructured mode:
   - rely on semantic chunks, overlap, lexical retrieval, adjacency links
   - build ChunkGraph
   - connect neighboring and semantically related chunks

3. Scanned/layout-heavy mode:
   - page-first processing
   - preserve page boundaries
   - optionally mark OCR confidence
   - build PageGraph
   - support page neighbor navigation

Important:
The system must not fail just because headings are weak. It should degrade gracefully into chunk/page-based retrieval.

Answering requirements:
Every answer response must contain:
- answer text
- evidence items used
- citations
- confidence label
- retrieval path summary
- whether agent loop was used

Confidence labels:
- direct_evidence
- multi_evidence_inference
- insufficient_evidence

Bounded custom agent design:
Implement our own ReAct-style retrieval loop from scratch.
Do NOT use agent libraries.

The loop should work like:
1. Observe current query + retrieved evidence summary
2. Think: is evidence sufficient?
3. If not sufficient, choose one action from allowed actions
4. Execute action
5. Update working memory
6. Stop when sufficient or limit reached

Allowed retrieval actions:
- search_lexical
- search_semantic
- search_structure
- fetch_node
- fetch_neighbors
- fetch_parent
- fetch_children
- follow_reference
- fetch_page
- fetch_table
- expand_same_section

The agent must be bounded:
- max steps from env
- max retrieval actions per query
- max cumulative context size
- cannot answer without evidence
- cannot freely hallucinate new tools
- must log reasoning summaries, but do not expose raw chain-of-thought
- store compact decision trace for debugging

Important note on reasoning:
Do not store or expose raw hidden chain-of-thought.
Instead, store safe structured reasoning summaries such as:
- why more retrieval was needed
- what action was chosen
- what gap it tried to fill
- why it stopped

Folder structure:
Create the project with this structure:

app/
  main.py
  core/
    config.py
    logging.py
    exceptions.py
    constants.py
  api/
    deps.py
    router.py
    v1/
      documents.py
      queries.py
      health.py
  schemas/
    common.py
    document.py
    query.py
    retrieval.py
    agent.py
  db/
    base.py
    session.py
    models/
      document.py
      page.py
      chunk.py
      graph_node.py
      graph_edge.py
      query_log.py
      answer_log.py
  repositories/
    document_repository.py
    page_repository.py
    chunk_repository.py
    graph_repository.py
    query_repository.py
  services/
    ingestion/
      ingest_service.py
      parser_service.py
      mode_detector.py
      chunk_service.py
      structure_extractor.py
      table_extractor.py
      reference_extractor.py
      summary_service.py
      embedding_service.py
      graph_builder.py
    retrieval/
      lexical_retriever.py
      semantic_retriever.py
      structure_retriever.py
      hybrid_retriever.py
      reranker.py
      citation_builder.py
    agent/
      react_loop.py
      state.py
      actions.py
      stop_conditions.py
      decision_trace.py
    qa/
      query_classifier.py
      sufficiency_checker.py
      answer_generator.py
      context_builder.py
    llm/
      provider.py
      openai_provider.py
      embedding_provider.py
    storage/
      file_store.py
  domain/
    enums.py
    types.py
    interfaces/
      graph_interface.py
      retriever_interface.py
      llm_interface.py
  utils/
    text.py
    tokens.py
    pdf.py
    ids.py
    time.py
tests/
  unit/
  integration/
alembic/
progress.md
.env.example
README.md

Database models:
Create SQLAlchemy models for:
1. Document
   - id
   - filename
   - content_type
   - mode
   - status
   - checksum
   - page_count
   - created_at
   - updated_at

2. Page
   - id
   - document_id
   - page_number
   - raw_text
   - summary
   - layout_type
   - ocr_confidence

3. Chunk
   - id
   - document_id
   - page_id nullable
   - chunk_index
   - text
   - normalized_text
   - section_title nullable
   - metadata_json
   - embedding vector
   - prev_chunk_id nullable
   - next_chunk_id nullable

4. GraphNode
   - id
   - document_id
   - node_type
   - title nullable
   - summary nullable
   - page_start nullable
   - page_end nullable
   - content_ref nullable
   - metadata_json

5. GraphEdge
   - id
   - document_id
   - from_node_id
   - to_node_id
   - edge_type
   - weight nullable
   - metadata_json

6. QueryLog
   - id
   - document_id nullable
   - query_text
   - query_type
   - used_agent boolean
   - retrieval_trace_json
   - created_at

7. AnswerLog
   - id
   - query_log_id
   - answer_text
   - confidence
   - citations_json
   - created_at

Enums:
Create enums for:
- DocumentMode: structured, semi_structured, unstructured, scanned
- DocumentStatus: uploaded, parsing, indexed, failed
- QueryType: fact, summary, comparison, clause, table, cross_reference, follow_up, multi_hop
- NodeType: section, subsection, page, table, chunk, appendix, note
- EdgeType: parent_child, neighbor, reference, semantic_link, page_link, section_link
- ConfidenceLabel: direct_evidence, multi_evidence_inference, insufficient_evidence

Common graph interface:
Create a common graph interface with methods like:
- search_candidates(query, top_k)
- fetch_node(node_id)
- fetch_neighbors(node_id)
- fetch_parent(node_id)
- fetch_children(node_id)
- follow_references(node_id)

Implement it for:
- TreeGraph behavior
- ChunkGraph behavior
- PageGraph behavior

API endpoints:
Build these REST APIs:

1. POST /api/v1/documents/upload
- multipart upload
- save file
- create document record
- trigger ingestion pipeline synchronously first, but structure it so background job support can be added later
- response:
  - document_id
  - filename
  - detected_mode
  - status
  - page_count

2. GET /api/v1/documents/{document_id}
- return document metadata

3. GET /api/v1/documents/{document_id}/status
- return indexing status and mode

4. GET /api/v1/documents/{document_id}/structure
- return extracted structure / graph summary

5. GET /api/v1/documents/{document_id}/pages/{page_number}
- return page text, page summary, and citations info

6. POST /api/v1/queries/ask
Request:
- document_id
- query
- conversation_context optional
- top_k optional
- allow_agent optional default true

Response:
- answer
- confidence
- citations
- evidence
- used_agent
- retrieval_trace_summary
- query_type

7. GET /api/v1/health
- basic health check

Query pipeline:
Implement this exact flow:
1. classify query
2. run hybrid retrieval:
   - lexical
   - semantic
   - structure-aware where available
3. rerank candidates
4. build evidence context
5. run sufficiency checker
6. if sufficient -> generate answer
7. else if allow_agent=true -> bounded ReAct loop
8. rerun sufficiency
9. generate answer or insufficient-evidence response
10. persist query and answer logs

Hybrid retrieval details:
Lexical retrieval:
- use BM25 or PostgreSQL full-text search
- must work well for exact phrase / rare term lookups

Semantic retrieval:
- embedding-based top-k search using pgvector

Structure retrieval:
- match section titles, summaries, appendix names, note labels, table labels

Hybrid merger:
- normalize scores
- merge deduplicated candidates
- keep provenance of which retriever found each candidate

Reranking:
Implement a reranker that scores candidates using:
- lexical match quality
- semantic relevance
- structural relevance
- page proximity
- query type bias

You may implement a simple deterministic reranker first with clear extension points for LLM reranking later.

Mode detection:
Implement a mode detector using heuristics like:
- heading density
- average line length variance
- repeated heading patterns
- page structure regularity
- OCR confidence if available
- table density

Do not overcomplicate first version. Keep it heuristic but modular.

Chunking:
Implement different chunking strategies:
- section-aware chunking for structured docs
- paragraph/sliding-window chunking for unstructured docs
- page-based chunking for scanned/layout-heavy docs

Citations:
Each citation should include:
- document_id
- page number or page range
- section title if available
- evidence snippet
- chunk/node identifiers

Sufficiency checker:
Create a dedicated module that decides:
- enough evidence or not
- what evidence is missing
- suggested next retrieval direction

Return structured output like:
- sufficient: bool
- reason: str
- missing_evidence_type: optional str
- suggested_actions: list[str]

Custom ReAct loop:
Implement from scratch with:
- AgentState
- Working memory
- Step counter
- Action registry
- Observation objects
- Decision trace summaries
- Stop conditions

Do not implement free-form unrestricted agenting.
Action selection may use deterministic rules first, with optional LLM-assisted action choice through our own provider interface.

LLM abstraction:
Create provider interfaces so LLM usage is swappable.
Include:
- generate_text(...)
- generate_structured(...)
- generate_embedding(...)

Add an initial provider implementation for one provider only, but keep the abstraction clean.

Important:
In .env.example, mention:
- LLM_PROVIDER
- LLM_MODEL
- LLM_ACCESS_TOKEN
I will fill them later.

Coding style:
- type hints everywhere
- docstrings on public functions
- no dead code
- no unnecessary abstraction
- minimal but clear comments
- proper exception handling
- consistent naming
- response models via Pydantic
- repository-service separation
- keep business logic out of route handlers

Implementation steps:
Phase 1:
- project bootstrap
- config
- DB models
- migrations
- health endpoint
- upload endpoint
- document metadata endpoint

Phase 2:
- parsing
- mode detection
- chunking
- graph building
- embeddings
- persistence

Phase 3:
- lexical retrieval
- semantic retrieval
- hybrid retrieval
- reranker
- query classify
- answer generation
- citations

Phase 4:
- sufficiency checker
- custom bounded ReAct loop
- agent actions
- decision trace
- query logging

Phase 5:
- tests
- README
- progress.md updates
- cleanup

README requirements:
Explain:
- architecture
- why no LangChain / LangGraph
- ingestion flow
- retrieval flow
- bounded agent loop
- env setup
- run commands
- migration commands
- API usage examples
- future extension points

Testing:
Add unit tests for:
- mode detector
- chunking
- graph builder
- hybrid retrieval merger
- sufficiency checker
- stop conditions

Add integration tests for:
- upload document
- index document
- ask query
- answer with citations
- insufficient evidence scenario

Security and robustness:
- validate file type
- file size guardrails
- safe temp file handling
- protect against huge context assembly
- cap retrieval sizes
- sanitize logged content where needed
- avoid leaking secrets
- graceful failure states

What I want from you:
1. Create the full backend codebase.
2. Create the folder structure above.
3. Implement the APIs.
4. Implement ingestion, indexing, retrieval, answer generation, and custom bounded ReAct loop.
5. Add .env.example with LLM and token placeholders.
6. Add progress.md and update it as you build.
7. Keep code practical, not overengineered.
8. Make sure it is easy for me to connect a frontend later.


Make sensible implementation choices and proceed. Make best possible solution ,use your expertise.


LLM tasks:
Task 1: “Result” is actually a Evaluation and suggestion side: once PRD is entered or uploaded let user to click on process PRD button in PRD section.
On precessing PRD using myRAG ,the llm shall edit Evaluation Parameters , determine what shall be the Evaluation Parameters .user may edit, add or remove there parameters.
What are Evaluation Parameters : user whats to evaluate the application he is building somewhere, to test he configures his apis to this application at (actual Data section).Based on 6 context layers and their out come he wants to understand how can he improve the response of his application, and what his AI response misses to have for the given PRD.

Task 2. Based on PRD determine what shall be the response to the “user input” (“user input ” is expected to be entered everytime when user wants to test his application AI response to particular “user prompt”) so  “Result” which is actually a Evaluation and suggestion side shall create its own system prompt based on PRD,store  what shall be stored in  state & Memory , use myRAG, conversation history ,tools(get these from actual data, sources are configured here) needed based on the user input. Now use these to evaluate the “Model Response” only, don't publish in any text box. And to evaluate “model Response” which is generated by LLM (configured in”configure LLM”) using context layers. The “Result” which is actually a Evaluation and suggestion side need to generate its own response to the “User Input” (using agent that -> create from scratch that shall use the elements generated in task 2 like system instruction/converation history-> use it as summary + last 5 conversation , myRAG , memory & state to generate response and compare it to “model Response”)
Instead when score Breakdown is hovered , show the insight, showing reason why this is the score and how it can be improved (after task 3).

Example :conversation history api gives 10 conversation , you can summarize and use . use configured DB to store the things and embeddings are expected to store in postgress, pg vector.
Task 3:Now once the response is generated “Model Response” need to be evaluated against the response generated by Result section and rate the “Model Response” considering the evaluation parameters generated in task , to do evaluation the result section response shall be compared to “model response”