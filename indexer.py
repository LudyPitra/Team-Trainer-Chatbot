import os
from dotenv import load_dotenv
import urllib.parse
from pymongo import MongoClient
from pymongo.server_api import ServerApi
from qdrant_client import QdrantClient
from llama_index.storage.docstore.mongodb import MongoDocumentStore
from llama_index.core import StorageContext
from llama_index.vector_stores.qdrant import QdrantVectorStore
from llama_index.core import SimpleDirectoryReader, VectorStoreIndex, Settings
from llama_index.core.node_parser import HierarchicalNodeParser, get_leaf_nodes
from llama_index.embeddings.ollama import OllamaEmbedding

# Load variables from .env file
load_dotenv()

MARKDOWN_DIR = "data/Markdown"
COLLECTION_NAME = "NovaMente"

MONGO_DB_NAME = "novamente_db"
MONGO_NAMESPACE = "docstore"

# Fetching environment variables with explicit 'str' typing and fail-fast
try:
    QDRANT_URL = os.environ["QDRANT_URL"]
    QDRANT_API_KEY = os.environ["QDRANT_API_KEY"]
    RAW_MONGO_URI = os.environ["MONGO_URI"]
except KeyError as e:
    raise ValueError(f"❌ Missing required environment variable in .env file: {e}")


def get_safe_mongo_uri(uri: str) -> str:
    """
    Safely encodes the password in the MongoDB URI if it contains special characters.
    """
    if "://" in uri and "@" in uri:
        # We split the URI to isolate the user:password part
        prefix, rest = uri.split("://", 1)
        user_pass, endpoint = rest.rsplit("@", 1)

        if ":" in user_pass:
            user, password = user_pass.split(":", 1)
            # Encode only the user and password parts
            safe_user = urllib.parse.quote_plus(user)
            safe_password = urllib.parse.quote_plus(password)
            return f"{prefix}://{safe_user}:{safe_password}@{endpoint}"

    return uri


MONGO_URI = get_safe_mongo_uri(RAW_MONGO_URI)


def reset_qdrant(client: QdrantClient):
    """Checks and deletes the Qdrant collection if it exists."""
    existing_collections = [c.name for c in client.get_collections().collections]

    if COLLECTION_NAME in existing_collections:
        print(f"🗑️ Qdrant collection '{COLLECTION_NAME}' found. Deleting...")
        client.delete_collection(COLLECTION_NAME)
        print("✅ Qdrant collection deleted successfully.")
    else:
        print(
            f"ℹ️ Qdrant collection '{COLLECTION_NAME}' doesn't exist. Creating from scratch."
        )


def reset_mongodb():
    """Connects directly to MongoDB Atlas and drops the docstore collection if it exists."""
    print("⏳ Checking MongoDB Atlas state...")
    client = MongoClient(MONGO_URI)
    db = client[MONGO_DB_NAME]

    if MONGO_NAMESPACE in db.list_collection_names():
        print(f"🗑️ MongoDB collection '{MONGO_NAMESPACE}' found. Deleting...")
        db.drop_collection(MONGO_NAMESPACE)
        print("✅ MongoDB collection deleted successfully.")
    else:
        print(
            f"ℹ️ MongoDB collection '{MONGO_NAMESPACE}' doesn't exist. Creating from scratch."
        )

    client.close()


def setup_databases():
    """Initializes connections, performs reset, and creates the StorageContext."""

    print("⏳ Connecting to Qdrant Cloud...")
    qdrant_client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)

    # 1. Clean the vector database and instantiate the VectorStore
    reset_qdrant(qdrant_client)
    vector_store = QdrantVectorStore(
        client=qdrant_client, collection_name=COLLECTION_NAME
    )

    # 2. Clean the document store and instantiate the MongoDocumentStore
    reset_mongodb()
    print("⏳ Connecting Document Store to MongoDB Atlas...")
    mongo_docstore = MongoDocumentStore.from_uri(
        uri=MONGO_URI, db_name=MONGO_DB_NAME, namespace=MONGO_NAMESPACE
    )

    print("⏳ Configuring the Storage Context...")
    storage_context = StorageContext.from_defaults(
        docstore=mongo_docstore, vector_store=vector_store
    )

    print("✅ Databases formatted and Storage Context established successfully!")
    return storage_context


def build_hierarchical_index(storage_context: StorageContext):
    """Reads Markdowns, creates hierarchical nodes, and indexes them."""

    print("⏳ Configuring Embedding Model (Qwen3)...")
    # Setting the embedding model globally so VectorStoreIndex can use it
    Settings.embed_model = OllamaEmbedding(
        model_name="qwen3-embedding:8b",
        base_url="http://localhost:11434",  # Change this if moving Ollama to the cloud
    )

    # We don't need the LLM for indexing, only for querying later
    Settings.llm = None

    print(f"⏳ Loading Markdown files from '{MARKDOWN_DIR}'...")
    documents = SimpleDirectoryReader(
        input_dir=MARKDOWN_DIR, required_exts=[".md"]
    ).load_data()

    if not documents:
        raise ValueError(
            f"❌ No Markdown files found in {MARKDOWN_DIR}. Run converter.py first!"
        )

    print(f"✅ Loaded {len(documents)} documents. Starting Hierarchical Chunking...")

    # Create the parser with Parent (2048 tokens) and Child (512 tokens) sizes
    node_parser = HierarchicalNodeParser.from_defaults(chunk_sizes=[2048, 512])

    # Parse documents into a tree of nodes
    nodes = node_parser.get_nodes_from_documents(documents)

    # Extract only the lowest level nodes (Children/Leaves)
    leaf_nodes = get_leaf_nodes(nodes)
    print(f"✅ Generated {len(nodes)} total nodes and {len(leaf_nodes)} leaf nodes.")

    print("⏳ Saving document structure (Parents & Children) to MongoDB...")
    # Add ALL nodes to the docstore (MongoDB) so it remembers the hierarchy
    storage_context.docstore.add_documents(nodes)

    print("⏳ Generating embeddings and saving leaf nodes to Qdrant...")
    # VectorStoreIndex automatically detects our Qdrant instance inside the storage_context
    index = VectorStoreIndex(
        nodes=leaf_nodes,
        storage_context=storage_context,
        show_progress=True,  # Shows a nice progress bar while generating embeddings!
    )

    print("🎉 Indexing completed successfully! The system is ready.")
    return index


if __name__ == "__main__":
    print("🚀 Starting Data Ingestion Pipeline...")
    storage_context = setup_databases()
    build_hierarchical_index(storage_context)
