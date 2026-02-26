from qdrant_client import QdrantClient
from llama_index.embeddings.ollama import OllamaEmbedding
from llama_index.core import Settings, VectorStoreIndex
from llama_index.vector_stores.qdrant import QdrantVectorStore
from llama_index.llms.ollama import Ollama
from dotenv import load_dotenv
import os

load_dotenv()

Settings.llm = Ollama(model="ministral-3:14b")
Settings.embed_model = OllamaEmbedding(
    model_name="mxbai-embed-large:latest",
)

client = QdrantClient(url=os.getenv("QDRANT_URL"), api_key=os.getenv("QDRANT_API_KEY"))

vector_store = QdrantVectorStore(client=client, collection_name="NovaMente")

index = VectorStoreIndex.from_vector_store(
    vector_store=vector_store,
)

query_engine = index.as_query_engine(
    similarity_top_k=5,
)


def retriever_tool(query: str):
    """
    Search for information in the NovaMente company documents.
    Use this tool to answer questions about company policies, benefits,
    culture, organizational structure, and any internal documentation.
    Input should be a plain text question.
    """

    response = query_engine.query(query)
    return response
