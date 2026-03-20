import os
import urllib.parse
from dotenv import load_dotenv
from datetime import datetime
from pymongo import MongoClient
from qdrant_client import QdrantClient
from llama_index.core.schema import NodeRelationship
from llama_index.storage.docstore.mongodb import MongoDocumentStore
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.core import StorageContext
from llama_index.vector_stores.qdrant import QdrantVectorStore
from llama_index.core import SimpleDirectoryReader, VectorStoreIndex, Settings
from llama_index.core.node_parser import HierarchicalNodeParser, get_leaf_nodes

load_dotenv()

MARKDOWN_DIR = "data/Markdown"
VERSION_FILE = "data/active_index.txt"

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

COLLECTION_NAME = f"NovaMente_{timestamp}"
MONGO_DB_NAME = "novamente_db"
MONGO_NAMESPACE = f"docstore_{timestamp}"

os.makedirs("data", exist_ok=True)
with open(VERSION_FILE, "w") as f:
    f.write(timestamp)

try:
    QDRANT_URL = os.environ["QDRANT_URL"]
    QDRANT_API_KEY = os.environ["QDRANT_API_KEY"]
    RAW_MONGO_URI = os.environ["MONGO_URI"]
    OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]
except KeyError as e:
    raise ValueError(f"❌ Missing required environment variable in .env file: {e}")


def get_safe_mongo_uri(uri: str) -> str:
    """
    Safely encodes the password in the MongoDB URI if it contains special characters.
    """
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


def cleanup_old_collections(qdrant_client: QdrantClient):
    """Delete old collections in Qdrant and MongoDB to save cloud storage space."""
    existing_qdrant = [c.name for c in qdrant_client.get_collections().collections]

    for coll in existing_qdrant:
        if coll.startswith("NovaMente_") and timestamp not in coll:
            print(f"🗑️ A apagar coleção antiga no Qdrant: {coll}")
            qdrant_client.delete_collection(coll)

    print("⏳ Checking MongoDB Atlas for cleanup.")

    mongo_client = MongoClient(MONGO_URI)

    try:
        db = mongo_client[MONGO_DB_NAME]
        existing_mongo = db.list_collection_names()

        for coll in existing_mongo:
            if "docstore_" in coll and timestamp not in coll:
                print(f"🗑️ Deleting an old collection in MongoDB: {coll}")
                db.drop_collection(coll)
    except Exception as e:
        print(f"❌ Error cleaning MongoDB: {e}")
    finally:
        mongo_client.close()


def setup_databases():
    """Initializes connections, performs reset, and creates the StorageContext."""
    print("⏳ Connecting to Qdrant Cloud...")
    qdrant_client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)

    cleanup_old_collections(qdrant_client)

    vector_store = QdrantVectorStore(
        client=qdrant_client, collection_name=COLLECTION_NAME
    )

    print("⏳ Connecting Document Store to MongoDB Atlas...")
    mongo_docstore = MongoDocumentStore.from_uri(
        uri=MONGO_URI, db_name=MONGO_DB_NAME, namespace=MONGO_NAMESPACE
    )

    storage_context = StorageContext.from_defaults(
        docstore=mongo_docstore, vector_store=vector_store
    )

    return storage_context


def build_hierarchical_index(storage_context: StorageContext):
    """Reads Markdowns, creates hierarchical nodes, and indexes them."""
    print("⏳ Configuring Embedding Model (OpenAI)...")
    Settings.embed_model = OpenAIEmbedding(
        model="text-embedding-3-small", api_key=OPENAI_API_KEY
    )

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

    node_parser = HierarchicalNodeParser.from_defaults(chunk_sizes=[2048, 512])

    nodes = node_parser.get_nodes_from_documents(documents)

    leaf_nodes = get_leaf_nodes(nodes)

    leaf_ids = {n.node_id for n in leaf_nodes}
    for node in nodes:
        if node.node_id not in leaf_ids:
            node.relationships.pop(NodeRelationship.PARENT, None)

    print(f"✅ Generated {len(nodes)} total nodes and {len(leaf_nodes)} leaf nodes.")

    print("⏳ Saving document structure (Parents & Children) to MongoDB...")

    storage_context.docstore.add_documents(nodes)

    print("⏳ Generating embeddings and saving leaf nodes to Qdrant...")

    index = VectorStoreIndex(
        nodes=leaf_nodes,
        storage_context=storage_context,
        show_progress=True,
    )

    print("🎉 Indexing completed successfully! The system is ready.")
    return index


if __name__ == "__main__":
    print("🚀 Starting Data Ingestion Pipeline...")
    storage_context = setup_databases()
    build_hierarchical_index(storage_context)
