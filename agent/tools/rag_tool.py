from qdrant_client import QdrantClient
from llama_index.embeddings.ollama import OllamaEmbedding
from llama_index.core import Settings, VectorStoreIndex
from llama_index.vector_stores.qdrant import QdrantVectorStore
from dotenv import load_dotenv
import os

load_dotenv()

Settings.embed_model = OllamaEmbedding(
    model_name="qwen3-embedding:8b",
)

client = QdrantClient(url=os.getenv("QDRANT_URL"), api_key=os.getenv("QDRANT_API_KEY"))

vector_store = QdrantVectorStore(client=client, collection_name="NovaMente")

index = VectorStoreIndex.from_vector_store(
    vector_store=vector_store,
)

retriever = index.as_retriever(similarity_top_k=25)


def retriever_tool(query: str):
    """
    Search for information in the NovaMente company documents.
    Use this tool to answer questions about company policies, benefits,
    culture, organizational structure, and any internal documentation.
    Input should be a plain text question.
    """

    nodes = retriever.retrieve(query)

    formatted_contexts = []

    for node in nodes:
        file_name = node.metadata.get("file_name", "Unknown_Document")

        session = node.metadata.get("header_path", "General Document")
        page = node.metadata.get("page_label", "")

        str_page = f" (Page {page})" if page else ""

        text = node.text

        formatted_block = (
            f"===[REFERENCE FOUND]===\n"
            f"File: {file_name}{str_page}\n"
            f"Session: {session}\n"
            f"Content: \n{text}\n"
        )

        formatted_contexts.append(formatted_block)

    final_response = "\n\n".join(formatted_contexts)

    return final_response
