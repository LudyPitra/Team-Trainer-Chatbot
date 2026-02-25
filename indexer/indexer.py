import os
from dotenv import load_dotenv
from qdrant_client import QdrantClient
from llama_index.core.node_parser import MarkdownNodeParser
from llama_index.readers.docling import DoclingReader
from llama_index.embeddings.ollama import OllamaEmbedding
from llama_index.core import StorageContext, VectorStoreIndex
from llama_index.vector_stores.qdrant import QdrantVectorStore

load_dotenv()

SOURCE = "/home/ludy-dev/Documents/02-Projects/LLM-for-company-teams/data/PDFs/"
EMBED_MODEL = "mxbai-embed-large"
SUPPORTED_EXTS = {".pdf", ".docx", ".md", ".csv", ".txt"}
COLLECTION_NAME = "NovaMente"

reader = DoclingReader()
node_parser = MarkdownNodeParser()
embed_model = OllamaEmbedding(model_name=EMBED_MODEL)


def get_qdrant_client():
    return QdrantClient(
        url=os.getenv("QDRANT_URL"), api_key=os.getenv("QDRANT_API_KEY")
    )


def reset_collection(client: QdrantClient):
    existing = [c.name for c in client.get_collections().collections]

    if COLLECTION_NAME in existing:
        print(f"🗑️ Collection {COLLECTION_NAME} was found. Deleting")
        client.delete_collection(COLLECTION_NAME)
        print("✅ Collection deleted")
    else:
        print(f"ℹ️Collection '{COLLECTION_NAME}' doesn't exist. Creating from scratch")


def load_documents(directory: str = SOURCE):

    if not os.path.exists(directory):
        raise FileNotFoundError(f"Directory not Found: {directory}")

    valid_files = []
    unsupported = []

    for file_name in os.listdir(directory):
        file_path = os.path.join(directory, file_name)

        if os.path.isdir(file_path):
            continue

        ext = os.path.splitext(file_name)[1].lower()

        if ext in SUPPORTED_EXTS:
            valid_files.append((file_name, ext))

        else:
            unsupported.append((file_name, ext))

    if unsupported:
        names = ", ".join(f"{n} ({e})" for n, e in unsupported)
        raise ValueError(f"Unsupported formats found: {names}")

    if not valid_files:
        raise ValueError(f"No valid files found in: {directory}")

    documents = []

    for file_name, _ in valid_files:
        file_path = os.path.join(directory, file_name)
        print(f"📄 Loading: {file_name}")
        documents.extend(reader.load_data(file_path))

    print(f"✅ {len(documents)} documents loaded.")
    return documents


def build_index(documents: list, client: QdrantClient):
    vector_store = QdrantVectorStore(client=client, collection_name=COLLECTION_NAME)
    storage_context = StorageContext.from_defaults(vector_store=vector_store)

    print("⏳Indexing documents...")
    index = VectorStoreIndex.from_documents(
        documents,
        storage_context=storage_context,
        transformations=[node_parser],
        embed_model=embed_model,
    )

    print("✅Indexing completed!")

    return index


def main():
    client = get_qdrant_client()
    reset_collection(client)
    documents = load_documents(SOURCE)
    build_index(documents, client)


if __name__ == "__main__":
    main()
