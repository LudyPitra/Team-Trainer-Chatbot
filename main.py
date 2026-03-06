import chainlit as cl
from agent.agent import agent
from llama_index.core.workflow import Context
from llama_index.core.agent.workflow import AgentStream


@cl.on_chat_start
async def start_session():
    ctx = Context(agent)
    cl.user_session.set("ctx", ctx)

    await cl.Message(
        content="👋 Hi! I'm the AI ​​Assistant at NovaMente. I can help with questions about company policies, benefits, structure, and culture. What would you like to know?",
        author="NovaMente Assistant",
    ).send()


@cl.on_message
async def answer_message(message: cl.Message):
    ctx = cl.user_session.get("ctx")
    msg = cl.Message(content="")
    await msg.send()

    try:
        handler = agent.run(message.content, ctx=ctx)
        async for event in handler.stream_events():
            if isinstance(event, AgentStream):
                await msg.stream_token(event.delta)
        await msg.update()

    except Exception as e:
        msg.content = f"⚠️A technical error occurred: {str(e)}"
        await msg.update()
