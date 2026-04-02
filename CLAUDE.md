# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

HR assistant chatbot for NovaMente company. Users chat via a frontend → Go gateway (port 8080) → Python FastAPI AI engine (port 8000). The AI engine uses LlamaIndex with RAG over 18 internal company documents stored in Qdrant (vectors) and Redis (full text).

## Architecture

```
Frontend → Go Gateway (8080) → FastAPI AI Engine (8000)
                                     ↓
                          LlamaIndex FunctionAgent
                          (gpt-4o-mini, system prompt)
                                     ↓
                          RAG Query Engine (rag_tool.py)
                          VectorRetriever (top-12) → AutoMerging → LLMRerank (top-3)
                                     ↓
                     Qdrant (embeddings) + Redis (full text)
```

**`gateway/`** — Go HTTP server. Manages sessions via HTTP-only cookies (`novamente_session`, UUID, 1hr expiry). Forwards `POST /api/chat` to the AI engine.

**`ai-engine/`** — Python FastAPI server. Maintains in-memory agent sessions (`Dict[UUID, {agent, ctx}]`). Endpoints: `POST /api/chat`, `DELETE /api/session/{session_id}`.

**`ai-engine/agent/bot.py`** — Creates `FunctionAgent` with the HR system prompt and the RAG tool.

**`ai-engine/agent/tools/rag_tool.py`** — RAG pipeline: VectorIndexRetriever (k=12) → AutoMergingRetriever → LLMRerank (top-n=3, gpt-4o-mini).

**`ai-engine/indexer.py`** — One-time pipeline to index documents. Parses Markdown into hierarchical nodes (2048/512 byte chunks, 50-byte overlap), pushes to Redis + Qdrant.

**`ai-engine/converter.py`** — Converts PDFs/DOCX to Markdown using Docling. Outputs to `data/Markdown/`.

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
QDRANT_URL=
QDRANT_API_KEY=
OPENAI_API_KEY=
REDIS_URI=
REDIS_HOST=
REDIS_PORT=
REDIS_PASSWORD=
```

## Key Design Decisions

- **Session state is in-memory only** in the FastAPI server — lost on restart. The Go gateway persists session identity via cookies.
- **LLM reranking** (not cross-encoder): `LLMRerank` with gpt-4o-mini filters retrieved nodes down to top-3 before feeding to the agent.
- **Auto-merging retrieval**: Hierarchical node structure allows merging child chunks back into parent context when most children are retrieved.
- **Model**: `gpt-4o-mini` is used for both the agent (temp=0.3) and the reranker (temp=0.1). Embeddings use `text-embedding-3-small`.
- **Python package manager**: `uv` (not pip). Use `uv run` to execute scripts.
