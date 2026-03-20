import os
import urllib.parse
from dotenv import load_dotenv
from qdrant_client import QdrantClient
from llama_index.storage.docstore.mongodb import MongoDocumentStore
from llama_index.core import StorageContext, VectorStoreIndex, Settings
from llama_index.vector_stores.qdrant import QdrantVectorStore
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.core.retrievers import AutoMergingRetriever, VectorIndexRetriever
from llama_index.core.query_engine import RetrieverQueryEngine
from llama_index.core.tools import QueryEngineTool, ToolMetadata
from llama_index.llms.openai import OpenAI

load_dotenv()

VERSION_FILE = "data/active_index.txt"

try:
    with open(VERSION_FILE, "r") as f:
        timestamp = f.read().strip()
except FileNotFoundError:
    raise ValueError(
        "❌ Index version file not found! Please run 'indexer.py' first to generate the databases."
    )

COLLECTION_NAME = f"NovaMente_{timestamp}"
MONGO_DB_NAME = "novamente_db"
MONGO_NAMESPACE = f"docstore_{timestamp}"
print(f"🔗 Connecting index version: {timestamp}")

try:
    QDRANT_URL = os.environ["QDRANT_URL"]
    QDRANT_API_KEY = os.environ["QDRANT_API_KEY"]
    RAW_MONGO_URI = os.environ["MONGO_URI"]
    OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]
except KeyError as e:
    raise ValueError(f"❌ Missing required environment variable in .env file: {e}")


def get_safe_mongo_uri(uri: str) -> str:
    """Safely encodes the password in the MongoDB URI."""
    if "://" in uri and "@" in uri:
        prefix, rest = uri.split("://", 1)
        user_pass, endpoint = rest.rsplit("@", 1)
        if ":" in user_pass:
            user, password = user_pass.split(":", 1)
            safe_user = urllib.parse.quote_plus(user)
            safe_password = urllib.parse.quote_plus(password)
            return f"{prefix}://{safe_user}:{safe_password}@{endpoint}"
    return uri


MONGO_URI = get_safe_mongo_uri(RAW_MONGO_URI)


def get_index() -> VectorStoreIndex:
    """Connects to cloud databases and loads the VectorStoreIndex in read-only mode."""
    print("⏳ Connecting to Cloud Databases (Read-Only)...")

    Settings.embed_model = OpenAIEmbedding(
        model="text-embedding-3-small", api_key=OPENAI_API_KEY
    )

    qdrant_client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)
    vector_store = QdrantVectorStore(
        client=qdrant_client, collection_name=COLLECTION_NAME
    )

    mongo_docstore = MongoDocumentStore.from_uri(
        uri=MONGO_URI, db_name=MONGO_DB_NAME, namespace=MONGO_NAMESPACE
    )

    storage_context = StorageContext.from_defaults(
        docstore=mongo_docstore, vector_store=vector_store
    )

    print("⏳ Loading existing Vector Index from Storage...")
    index = VectorStoreIndex.from_vector_store(
        vector_store=vector_store, storage_context=storage_context
    )

    print("✅ Index loaded successfully from the cloud!")
    return index


def get_rag_tool() -> QueryEngineTool:
    """Create the Auto-Merging Retriever and wrap it in a QueryEngineTool for the agent."""
    Settings.llm = OpenAI(model="gpt-5-mini", api_key=OPENAI_API_KEY, temperature=0.0)

    index = get_index()

    print("⏳ Configuring the Auto-Merging Retriever...")

    base_retriever = VectorIndexRetriever(index=index, similarity_top_k=6)

    retriever = AutoMergingRetriever(
        vector_retriever=base_retriever,
        storage_context=index.storage_context,
        verbose=True,
    )

    query_engine = RetrieverQueryEngine.from_args(retriever)

    rag_tool = QueryEngineTool(
        query_engine=query_engine,
        metadata=ToolMetadata(
            name="company_knowledge_base",
            description=(
                "Use this tool to search ALL official information about the company NovaMente, "
                "including HR policies, benefits, history, rules, equipment, and internal procedures."
                "ALWAYS use this tool before answering questions about the company."
            ),
        ),
    )

    print("✅ RAG Tool created successfully!")
    return rag_tool


if __name__ == "__main__":
    print("🚀 Starting RAG Tool test...")
    tool = get_rag_tool()

    query = "What is our core values?"
    print(f"🔍 Querying the RAG Tool with: '{query}'")

    print("🔍 Searching the knowledge base...")

    response = tool.call(input=query)
    print("✅ RAG Tool Response:", response)
