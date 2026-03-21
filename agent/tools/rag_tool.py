import os
from dotenv import load_dotenv
from qdrant_client import QdrantClient
from llama_index.core.storage.docstore import SimpleDocumentStore
from llama_index.core import StorageContext, VectorStoreIndex, Settings
from llama_index.vector_stores.qdrant import QdrantVectorStore
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.core.retrievers import AutoMergingRetriever, VectorIndexRetriever
from llama_index.core.query_engine import RetrieverQueryEngine
from llama_index.core.tools import QueryEngineTool, ToolMetadata
from llama_index.core import PromptTemplate
from llama_index.postprocessor.sbert_rerank import SentenceTransformerRerank
from llama_index.llms.openai import OpenAI

load_dotenv()

DOCSTORE_FILE = "data/docstore.json"
COLLECTION_NAME = "NovaMente_Base"

try:
    QDRANT_URL = os.environ["QDRANT_URL"]
    QDRANT_API_KEY = os.environ["QDRANT_API_KEY"]
    OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]
except KeyError as e:
    raise ValueError(f"❌ Missing required environment variable in .env file: {e}")


def get_index():
    """Loads Qdrant from the cloud and the local DocStore tree."""
    print("⏳ Connecting to Cloud Qdrant and Local DocStore...")

    Settings.embed_model = OpenAIEmbedding(
        model="text-embedding-3-small", api_key=OPENAI_API_KEY
    )

    qdrant_client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)

    vector_store = QdrantVectorStore(
        client=qdrant_client, collection_name=COLLECTION_NAME
    )

    if not os.path.exists(DOCSTORE_FILE):
        raise FileNotFoundError(
            f"❌ '{DOCSTORE_FILE}' not found. Run indexer.py first!"
        )

    docstore = SimpleDocumentStore.from_persist_path(DOCSTORE_FILE)

    storage_context = StorageContext.from_defaults(
        docstore=docstore, vector_store=vector_store
    )

    print("⏳ Loading existing Vector Index...")

    index = VectorStoreIndex.from_vector_store(
        vector_store=vector_store, storage_context=storage_context
    )

    print("✅ Index loaded successfully!")
    return index
