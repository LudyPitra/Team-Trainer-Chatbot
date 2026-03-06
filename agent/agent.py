from llama_index.core import Settings
from llama_index.llms.ollama import Ollama
from llama_index.core.agent.workflow import FunctionAgent
from llama_index.core.workflow import Context
from agent.tools.rag_tool import retriever_tool
from pathlib import Path

Settings.llm = Ollama(
    model="qwen3.5:9b", request_timeout=300.0, context_window=8192, temperature=0.0
)

BASE_DIR = Path(__file__).resolve().parent.parent

prompt_path = BASE_DIR / "prompts" / "system_prompt.txt"
with open(prompt_path, "r", encoding="utf-8") as file:
    system_prompt = file.read()

agent = FunctionAgent(tools=[retriever_tool], system_prompt=system_prompt)

ctx = Context(agent)


async def main():
    try:
        while True:
            print("\n" + "-" * 60)

            prompt = input("Me: ").strip()

            if not prompt:
                continue

            if prompt.lower() == "exit":
                break

            response = await agent.run(prompt, ctx=ctx)
            print(response)

    except KeyboardInterrupt:
        print("\n\n⚠️Interrupted by user")
    finally:
        print("\n 👋 See you later")


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
