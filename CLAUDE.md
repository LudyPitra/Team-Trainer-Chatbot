# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

HR assistant chatbot for NovaMente company. Users chat via a frontend → Go gateway (port 8080) → Python FastAPI AI engine (port 8000). The AI engine uses LlamaIndex with RAG over 18 internal company documents stored in Qdrant (vectors) and Redis (full text). No frontend code exists in this repo — the frontend is external.

## Architecture

```
Frontend → Go Gateway (8080) → FastAPI AI Engine (8000)
                                     ↓
                          LlamaIndex FunctionAgent (name: "HR_Assistant")
                          (gpt-4o-mini, temp=0.3, system prompt from prompts/system_prompt.txt)
                                     ↓
                          RAG Query Engine (rag_tool.py)
                          VectorRetriever (top-12) → AutoMerging → LLMRerank (top-3)
                                     ↓
                     Qdrant collection "novamente_knowledge_base" + Redis (full text)
```

**`gateway/`** — Go HTTP server (module: `github.com/LudyPitra/Team-Trainer-Chatbot/gateway`). Manages sessions via HTTP-only cookies (`novamente_session`, UUID, 1hr expiry). Routes: `GET /ping` (health), `POST /api/chat`. 30s HTTP client timeout. Forwards requests to the AI engine with `session_id` added to JSON payload.

**`ai-engine/`** — Python FastAPI server. RAG engine is initialized as a singleton at startup via FastAPI lifespan. Maintains in-memory agent sessions (`Dict[UUID, {agent, ctx}]`). Endpoints: `POST /api/chat` (body: `{session_id, message}`), `DELETE /api/session/{session_id}`.

**`ai-engine/agent/bot.py`** — Creates `FunctionAgent` named `"HR_Assistant"` with system prompt loaded from `prompts/system_prompt.txt` (fallback: hardcoded string). Single tool: `QueryEngineTool` wrapping the RAG engine. Also has an interactive CLI mode for direct testing.

**`ai-engine/agent/tools/rag_tool.py`** — RAG pipeline: VectorIndexRetriever (k=12) → AutoMergingRetriever → LLMRerank (top-n=3, gpt-4o-mini, temp=0.1). Loads env vars via `python-dotenv`. Optional `DEBUG=true` for verbose node logging.

**`ai-engine/indexer.py`** — One-time pipeline to index documents. Clears Qdrant collection and flushes Redis before re-indexing. Parses Markdown into hierarchical nodes (chunk sizes: [2048, 512], overlap: 50 bytes), stores all nodes in Redis, pushes only leaf nodes to Qdrant for vectorization.

**`ai-engine/converter.py`** — Converts source files (`.pdf`, `.docx`, `.md`, `.csv`, `.txt`) from `data/PDFs/` to Markdown using `DoclingReader`. Outputs to `data/Markdown/`.

**`ai-engine/prompts/system_prompt.txt`** — HR assistant persona, tone guidelines, and instructions for the FunctionAgent.

**`ai-engine/data/`** — Contains `PDFs/` (source documents), `Markdown/` (18 converted HR policy files), `docstore.json` (local docstore cache), and `active_index.txt` (last index timestamp).

## Indexed Documents (18 NovaMente HR policies)

Located in `ai-engine/data/Markdown/`: Mission/Vision/Values, Company History & Culture, Organizational Structure, Employee Handbook, Benefits, Compensation & Career Levels, Vacation/Leave, Recruitment, Training & Development, Code of Ethics, Anti-discrimination & Diversity, LGPD Data Privacy, Information Security, Equipment & Technology Use, Health & Safety, Internal Regulations, Internal Communication, Standard Operating Procedures.

## Commands

### AI Engine (Python)

```bash
cd ai-engine

# Install dependencies (uses uv)
uv sync

# Run FastAPI server (dev mode with reload)
uv run uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# Index documents (run once after adding/changing documents)
uv run python indexer.py

# Convert PDFs/DOCX to Markdown (run before indexing)
uv run python converter.py

# Test RAG tool directly
uv run python agent/tools/rag_tool.py

# Test agent directly
uv run python agent/bot.py
```

### Gateway (Go)

```bash
cd gateway

# Run gateway server
go run main.go

# Build binary
go build -o gateway main.go
```

### Environment Setup

```bash
# Install all tool versions (Go, Python 3.12, Node LTS)
mise install
```

## Environment Variables

Required in `ai-engine/.env`:

```
QDRANT_URL=          # Qdrant cloud endpoint
QDRANT_API_KEY=      # Qdrant JWT auth token
OPENAI_API_KEY=      # Used for gpt-4o-mini (agent + reranker) and text-embedding-3-small
REDIS_URI=           # Full Redis connection URI (used by indexer.py)
REDIS_HOST=          # Redis hostname (used by rag_tool.py)
REDIS_PORT=          # Redis port
REDIS_PASSWORD=      # Redis auth password
DEBUG=               # Optional: "true" for verbose RAG node logging
```

## Key Design Decisions

- **Session state is in-memory only** in the FastAPI server — lost on restart. The Go gateway persists session identity via cookies.
- **LLM reranking** (not cross-encoder): `LLMRerank` with gpt-4o-mini filters retrieved nodes down to top-3 before feeding to the agent.
- **Auto-merging retrieval**: Hierarchical node structure allows merging child chunks back into parent context when most children are retrieved.
- **Model**: `gpt-4o-mini` is used for both the agent (temp=0.3) and the reranker (temp=0.1). Embeddings use `text-embedding-3-small`.
- **Python package manager**: `uv` (not pip). Use `uv run` to execute scripts.
- **RAG singleton**: The query engine is built once at FastAPI startup (lifespan) and shared across all sessions.
- **Indexer is destructive**: Running `indexer.py` deletes the existing Qdrant collection and flushes Redis before re-indexing.
- **`REDIS_URI` vs `REDIS_HOST/PORT/PASSWORD`**: `indexer.py` uses `REDIS_URI`; `rag_tool.py` uses individual host/port/password vars.
- **`llama-index-node-parser-docling`**: Listed as a dependency in `pyproject.toml` but not used in current code.
