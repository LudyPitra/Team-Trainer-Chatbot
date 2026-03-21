import os
from dotenv import load_dotenv
from qdrant_client import QdrantClient
from llama_index.core.storage.docstore import SimpleDocumentStore
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.core import StorageContext
from llama_index.vector_stores.qdrant import QdrantVectorStore
from llama_index.core import SimpleDirectoryReader, VectorStoreIndex, Settings
from llama_index.core.node_parser import HierarchicalNodeParser, get_leaf_nodes
from llama_index.core.schema import NodeRelationship

load_dotenv()

MARKDOWN_DIR = "data/Markdown"
DOCSTORE_FILE = "data/docstore.json"
COLLECTION_NAME = "NovaMente"

os.makedirs("data", exist_ok=True)

try:
    QDRANT_URL = os.environ["QDRANT_URL"]
    QDRANT_API_KEY = os.environ["QDRANT_API_KEY"]
    OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]
except KeyError as e:
    raise ValueError(f"❌ Missing required environment variable in .env file: {e}")


def reset_qdrant(qdrant_client: QdrantClient):
    """Clear the collection in Qdrant to ensure a fresh start with each indexing."""
    existing_collections = [c.name for c in qdrant_client.get_collections().collections]

    if COLLECTION_NAME in existing_collections:
        print(f"Deleting an old collection in Qdrant: {COLLECTION_NAME}")
        qdrant_client.delete_collection(collection_name=COLLECTION_NAME)


def setup_database():
    print("⏳ Connecting to Qdrant Cloud...")
    qdrant_client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)

    reset_qdrant(qdrant_client)

    vector_store = QdrantVectorStore(
        client=qdrant_client, collection_name=COLLECTION_NAME
    )

    print("⏳ Creating Local Document Store...")

    docstore = SimpleDocumentStore()

    storage_context = StorageContext.from_defaults(
        docstore=docstore, vector_store=vector_store
    )

    return storage_context


def build_hierarchical_index(storage_context: StorageContext):
    print("⏳ Building hierarchical index...")

    Settings.embed_model = OpenAIEmbedding(
        model="text-embedding-3-small", api_key=OPENAI_API_KEY
    )

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

    storage_context.docstore.persist(persist_path=DOCSTORE_FILE)

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
    storage_context = setup_database()
    build_hierarchical_index(storage_context)
