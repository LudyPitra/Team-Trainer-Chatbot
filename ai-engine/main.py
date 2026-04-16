import sys
import os
import json
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent))

import redis
from contextlib import asynccontextmanager
from uuid import UUID
from agent.tools.rag_tool import get_rag_query_engine
from agent.bot import create_agent
from fastapi.responses import StreamingResponse
from llama_index.core.agent.workflow import AgentStream
from llama_index.core.workflow import Context
from fastapi import FastAPI, HTTPException, Response, status, Request
from pydantic import BaseModel
import uvicorn


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("API server is starting up...")
    app.state.query_engine = get_rag_query_engine()
    print("RAG Query Engine initialized and ready.")

    app.state.agent = create_agent(app.state.query_engine)
    print("Agent initialized and ready to handle requests.")

    print("Connecting to Redis...")
    app.state.redis = redis.Redis(
        host=os.environ["REDIS_HOST"],
        port=int(os.environ["REDIS_PORT"]),
        password=os.environ["REDIS_PASSWORD"],
        username="default",
        decode_responses=True,
    )
    yield

    print("Closing Redis connection...")
    app.state.redis.close()
    print("API server is shutting down...")


app = FastAPI(
    title="Agent API",
    description="API for interacting with the agent",
    version="1.0.0",
    lifespan=lifespan,
)


@app.middleware("http")
async def verify_api_key(request: Request, call_next):
    api_key = os.environ.get("INTERNAL_API_KEY")
    if request.headers.get("X-Internal-Key") != api_key:
        return Response("Unauthorized", status_code=401)
    return await call_next(request)


class ChatRequest(BaseModel):
    session_id: UUID
    message: str


class ChatResponse(BaseModel):
    reply: str


@app.post("/api/chat")
async def chat_endpoint(request: ChatRequest):
    try:
        key = f"session:{request.session_id}"

        data = app.state.redis.get(key)

        if data:
            ctx = Context.from_dict(app.state.agent, json.loads(data))
        else:
            ctx = Context(app.state.agent)

        handler = app.state.agent.run(request.message, ctx=ctx)

        async def stream():
            async for response in handler.stream_events():
                if isinstance(response, AgentStream):
                    yield f"data: {response.delta}\n\n"

            await handler
            app.state.redis.set(key, json.dumps(ctx.to_dict()), ex=3600)

        return StreamingResponse(stream(), media_type="text/event-stream")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/session/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_session(session_id: UUID):
    """Remove the session from RAM to free up resources."""

    key = f"session:{session_id}"
    deleted = app.state.redis.delete(key)

    if deleted:
        print(f"Session {session_id} deleted from Redis.")
    else:
        print(f"Session {session_id} not found in Redis.")

    return Response(status_code=status.HTTP_204_NO_CONTENT)


if __name__ == "__main__":
    print("Starting API server on http://localhost:8000")
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
