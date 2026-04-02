import asyncio
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

# LlamaIndex Imports
from llama_index.core import Settings
from llama_index.llms.openai import OpenAI
from llama_index.core.agent.workflow import FunctionAgent
from llama_index.core.workflow import Context
from llama_index.core.tools import QueryEngineTool, ToolMetadata

from agent.tools.rag_tool import get_rag_query_engine

Settings.llm = OpenAI(model="gpt-4o-mini", temperature=0.3)

BASE_DIR = Path(__file__).resolve().parent.parent


def create_agent(query_engine):
    print("Initializing Agent and Tools...")

    rag_tool = QueryEngineTool(
        query_engine=query_engine,
        metadata=ToolMetadata(
            name="novamente_knowledge_base_query",
            description=(
                "Use this tool ALWAYS when the user asks questions about the NovaMente company, "
                "its values, culture, HR rules, benefits, or history. "
                "Pass the user's question clearly and directly."
            ),
        ),
    )

    prompt_path = BASE_DIR / "prompts" / "system_prompt.txt"
    try:
        with open(prompt_path, "r", encoding="utf-8") as file:
            system_prompt = file.read()
    except FileNotFoundError:
        system_prompt = "You are a helpful HR assistant for the NovaMente company."

    agent = FunctionAgent(
        name="HR_Assistant",
        description="Assistant for NovaMente HR matters",
        system_prompt=system_prompt,
        tools=[rag_tool],
        llm=Settings.llm,
    )

    return agent


async def main(agent, ctx):
    print("\n" + "-" * 60)
    print("Agent is ready! Type your questions below.")
    print("(Type 'exit' to stop the test)\n")

    try:
        while True:
            prompt = input("Me: ").strip()

            if not prompt:
                continue

            if prompt.lower() == "exit":
                break

            print("\nThinking...")
            response = await agent.run(prompt, ctx=ctx)
            print(f"\nNovaMente Assistant: {response}")
            print("-" * 60)

    except KeyboardInterrupt:
        print("\n\n⚠️ Interrupted by user")
    finally:
        print("\n 👋 See you later")


if __name__ == "__main__":
    engine = get_rag_query_engine()
    agent = create_agent(engine)
    ctx = Context(agent)
    asyncio.run(main(agent, ctx))
