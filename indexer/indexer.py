import os
from dotenv import load_dotenv
from qdrant_client import QdrantClient
from llama_index.core.readers.base import BaseReader
from llama_index.core.node_parser import MarkdownNodeParser
from llama_index.readers.docling import DoclingReader
from llama_index.embeddings.ollama import OllamaEmbedding
from llama_index.core import StorageContext, VectorStoreIndex, SimpleDirectoryReader
from llama_index.vector_stores.qdrant import QdrantVectorStore

load_dotenv()

SOURCE = "/home/ludy-dev/Documents/02-Projects/LLM-for-company-teams/data/PDFs/"
EMBED_MODEL = "qwen3-embedding:8b"
SUPPORTED_EXTS = {".pdf", ".docx", ".md", ".csv", ".txt"}
COLLECTION_NAME = "NovaMente"

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

    print("⏳Reading the directory to inject metadata automaticaly")

    docling_reader = DoclingReader()

    file_extractor: dict[str, BaseReader] = {
        ext: docling_reader for ext in SUPPORTED_EXTS
    }

    reader = SimpleDirectoryReader(
        input_dir=directory,
        required_exts=list(SUPPORTED_EXTS),
        file_extractor=file_extractor,
        recursive=False,
    )

    documents = reader.load_data()
    print(f"✅{len(documents)} documents loaded.")
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
