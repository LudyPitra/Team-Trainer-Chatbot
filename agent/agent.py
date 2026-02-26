from llama_index.core import Settings
from llama_index.llms.ollama import Ollama
from llama_index.core.agent.workflow import FunctionAgent
from tools.rag_tool import retriever_tool

Settings.llm = Ollama(model="ministral-3:14b")

system_prompt = """
You are NovaMente Assistant, an internal AI assistant designed to help employees 
find information about company policies, benefits, culture, and internal procedures.

Your responsibilities:
- Answer questions about HR policies, benefits, vacation, and compensation
- Provide information about organizational structure and internal procedures
- Guide employees to the correct information based on official company documents

Your behavior:
- Always base your answers on the official company documents available to you
- Be clear and objective, using simple and professional language
- If you don't find the information in the documents, say so honestly and suggest 
  the employee contact the HR department directly
- Never invent or assume information that is not present in the documents
- Always answer in the same language as the question
  """

workflow = FunctionAgent(tools=[retriever_tool], system_prompt=system_prompt)


async def main():
    query = ""
    response = await workflow.run(query)
    print(response)


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
