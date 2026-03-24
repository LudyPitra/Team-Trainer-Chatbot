import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent))

from agent.bot import create_agent
from llama_index.core.workflow import Context

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn

app = FastAPI(
    title="Agent API",
    description="API for interacting with the agent",
    version="1.0.0",
)

print("Loading agent and connecting to database...")

agent = create_agent()


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    reply: str


@app.post("/api/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    try:
        ctx = Context(agent)

        response = await agent.run(request.message, ctx=ctx)

        return ChatResponse(reply=str(response))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    print("Starting API server on http://localhost:8000")
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
