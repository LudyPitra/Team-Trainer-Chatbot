import sys
from pathlib import Path
from typing import Dict, Any
from uuid import UUID

sys.path.append(str(Path(__file__).resolve().parent))

from agent.bot import create_agent
from llama_index.core.workflow import Context

from fastapi import FastAPI, HTTPException, Response, status
from pydantic import BaseModel
import uvicorn

app = FastAPI(
    title="Agent API",
    description="API for interacting with the agent",
    version="1.0.0",
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

            new_agent = create_agent()
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

    if delete_session:
        print(f"Cleanup: Session {session_id} has been removed from RAM.")
    else:
        print(f"Cleanup: Session {session_id} not found, nothing to delete.")

    return Response(status_code=status.HTTP_204_NO_CONTENT)


if __name__ == "__main__":
    print("Starting API server on http://localhost:8000")
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
