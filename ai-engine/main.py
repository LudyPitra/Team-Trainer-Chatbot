import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent))

from typing import Dict, Any
from contextlib import asynccontextmanager
from uuid import UUID
from agent.tools.rag_tool import get_rag_query_engine
from agent.bot import create_agent
from llama_index.core.workflow import Context
from fastapi import FastAPI, HTTPException, Response, status
from pydantic import BaseModel
import uvicorn


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("API server is starting up...")
    app.state.query_engine = get_rag_query_engine()
    print("RAG Query Engine initialized and ready.")
    yield

    print("API server is shutting down...")


app = FastAPI(
    title="Agent API",
    description="API for interacting with the agent",
    version="1.0.0",
    lifespan=lifespan,
)

active_sessions: Dict[UUID, Any] = {}


class ChatRequest(BaseModel):
    session_id: UUID
    message: str


class ChatResponse(BaseModel):
    reply: str


@app.post("/api/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    try:
        if request.session_id not in active_sessions:
            print(f"Creating new session for ID: {request.session_id}")

            new_agent = create_agent(app.state.query_engine)
            new_ctx = Context(new_agent)

            active_sessions[request.session_id] = {"agent": new_agent, "ctx": new_ctx}

        session_data = active_sessions[request.session_id]
        agent = session_data["agent"]
        ctx = session_data["ctx"]

        response = await agent.run(request.message, ctx=ctx)

        return ChatResponse(reply=str(response))

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/session/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_session(session_id: UUID):
    """Remove the session from RAM to free up resources."""

    deleted_session = active_sessions.pop(session_id, None)

    if deleted_session:
        print(f"Cleanup: Session {session_id} has been removed from RAM.")
    else:
        print(f"Cleanup: Session {session_id} not found, nothing to delete.")

    return Response(status_code=status.HTTP_204_NO_CONTENT)


if __name__ == "__main__":
    print("Starting API server on http://localhost:8000")
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
