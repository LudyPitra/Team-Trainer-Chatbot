from llama_index.core import (
    SimpleDirectoryReader,
    VectorStoreIndex,
    StorageContext,
    Settings,
)
from llama_index.core.node_parser import MarkdownNodeParser
from llama_index.vector_stores.qdrant import QdrantVectorStore
from llama_index.embeddings.ollama import OllamaEmbedding
import qdrant_client


def test_retrieval(input_dir: str, query_text: str):
    print("1. Carregando e fatiando os documentos (Markdown -> Nodes)...")
    documents = SimpleDirectoryReader(input_dir, required_exts=[".md"]).load_data()
    nodes = MarkdownNodeParser().get_nodes_from_documents(documents)

    print("2. Configurando o modelo de Embeddings no Ollama...")
    embed_model = OllamaEmbedding(
        model_name="qwen3-embedding:8b", base_url="http://localhost:11434"
    )
    Settings.embed_model = embed_model
    Settings.llm = None

    print(
        "3. Inicializando Qdrant em memória e criando o índice (isso pode levar alguns segundos)..."
    )
    client = qdrant_client.QdrantClient(location=":memory:")
    vector_store = QdrantVectorStore(client=client, collection_name="test_novamente")
    storage_context = StorageContext.from_defaults(vector_store=vector_store)

    index = VectorStoreIndex(nodes, storage_context=storage_context)

    print(f"\n4. Realizando busca de teste para a pergunta: '{query_text}'")
    retriever = index.as_retriever(similarity_top_k=3)
    results = retriever.retrieve(query_text)

    print("\n=== RESULTADOS DA BUSCA VETORIAL ===")
    for i, res in enumerate(results, 1):
        print(f"\nRANK {i} | Score de Similaridade: {res.score:.4f}")
        print(f"Fonte: {res.node.metadata.get('file_name')}")
        # Aumentamos para 800 caracteres para tentar ler os 5 valores completos no output
        print(f"Trecho: {res.node.text}...\n{'-' * 40}")


if __name__ == "__main__":
    MD_DIR = "data/Markdown"

    # A query exata que você pediu para testarmos
    TEST_QUERY = "What are our core values?"

    test_retrieval(MD_DIR, TEST_QUERY)
