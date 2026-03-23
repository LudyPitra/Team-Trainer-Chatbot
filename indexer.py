import os
import redis
from dotenv import load_dotenv

# LlamaIndex imports
from llama_index.core import (
    SimpleDirectoryReader,
    StorageContext,
    VectorStoreIndex,
    Settings,
)
from llama_index.core.node_parser import HierarchicalNodeParser, get_leaf_nodes
from llama_index.embeddings.openai import OpenAIEmbedding

# Database imports
from llama_index.vector_stores.qdrant import QdrantVectorStore
from llama_index.storage.docstore.redis import RedisDocumentStore
import qdrant_client

# Load environment variables (.env)
load_dotenv()

# Configure the global Embedding model
Settings.embed_model = OpenAIEmbedding(model="text-embedding-3-small")


def main():
    print("Starting cloud indexing (Qdrant + Redis)...")

    # Configure Cloud Connections
    qdrant_url = os.environ["QDRANT_URL"]
    qdrant_api_key = os.environ["QDRANT_API_KEY"]

    # NOVAS VARIÁVEIS DO REDIS
    redis_host = os.environ["REDIS_HOST"]
    redis_port = int(os.environ["REDIS_PORT"])  # Convertendo para inteiro
    redis_password = os.environ["REDIS_PASSWORD"]

    collection_name = "novamente_knowledge_base"

    # --- DATABASE CLEANUP & CONNECTION STEP ---

    # Qdrant Cleanup
    print("Checking existing Qdrant collections...")
    client = qdrant_client.QdrantClient(url=qdrant_url, api_key=qdrant_api_key)

    if client.collection_exists(collection_name=collection_name):
        print(f"Collection '{collection_name}' found. Deleting for a clean index...")
        client.delete_collection(collection_name=collection_name)
    else:
        print(
            f"Collection '{collection_name}' does not exist. A new one will be created."
        )

    # Redis Connection & Cleanup (Usando o padrão da documentação)
    print("Connecting to Redis Cloud...")
    r_client = redis.Redis(
        host=redis_host,
        port=redis_port,
        password=redis_password,
        username="default",
        decode_responses=True,  # Facilita a leitura de strings em vez de bytes
    )

    print("Flushing existing Redis data...")
    r_client.flushdb()
    print("Redis database flushed successfully.")

    # -----------------------------

    # Initialize Vector Store (Qdrant)
    vector_store = QdrantVectorStore(client=client, collection_name=collection_name)

    # Initialize Document Store (Redis) passando o client explícito
    docstore = RedisDocumentStore.from_redis_client(redis_client=r_client)

    # Combine everything in the Storage Context
    storage_context = StorageContext.from_defaults(
        vector_store=vector_store, docstore=docstore
    )

    # Configure Hierarchical Node Parser
    node_parser = HierarchicalNodeParser.from_defaults(
        chunk_sizes=[2048, 512], chunk_overlap=50
    )

    # Load the Markdown documents
    print("Reading Markdown documents...")
    documents = SimpleDirectoryReader("./data/Markdown").load_data()

    # Process Nodes
    print("Generating node hierarchy...")
    nodes = node_parser.get_nodes_from_documents(documents)
    leaf_nodes = get_leaf_nodes(nodes)

    print(f"Total generated nodes (Parents + Children): {len(nodes)}")
    print(f"Total leaf nodes (Children): {len(leaf_nodes)}")

    # Save to Redis and Qdrant
    print("Sending full text to Redis Cloud...")
    storage_context.docstore.add_documents(nodes)

    print("Vectorizing and sending leaf nodes to Qdrant Cloud...")
    index = VectorStoreIndex(
        leaf_nodes, storage_context=storage_context, show_progress=True
    )

    print("Indexing completed successfully! Data is now in the cloud.")


if __name__ == "__main__":
    main()
