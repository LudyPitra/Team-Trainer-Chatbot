import os
import json
from dotenv import load_dotenv
from qdrant_client import QdrantClient
from llama_index.core import Settings, VectorStoreIndex
from llama_index.vector_stores.qdrant import QdrantVectorStore
from llama_index.embeddings.ollama import OllamaEmbedding

load_dotenv()

# 1. Configuramos APENAS o modelo de embedding (não precisamos do LLM aqui)
Settings.embed_model = OllamaEmbedding(
    model_name="qwen3-embedding:8b",
)

# 2. Conectamos ao Qdrant da mesma forma que no seu rag_tool.py
client = QdrantClient(url=os.getenv("QDRANT_URL"), api_key=os.getenv("QDRANT_API_KEY"))
vector_store = QdrantVectorStore(client=client, collection_name="NovaMente")
index = VectorStoreIndex.from_vector_store(vector_store=vector_store)

# 3. Aqui está o segredo: usamos as_retriever() em vez de as_query_engine()
# Coloquei top_k=10 para vermos uma margem maior de resultados
retriever = index.as_retriever(similarity_top_k=5)


def testar_query(pergunta: str):
    print(f"\n{'=' * 50}")
    print(f"🔍 BUSCANDO POR: '{pergunta}'")
    print(f"{'=' * 50}")

    # Fazemos a busca isolada
    nodes = retriever.retrieve(pergunta)

    for i, node in enumerate(nodes):
        score = node.score if node.score is not None else 0.0

        print(f"\n{'=' * 60}")
        print(f"📄 Chunk {i + 1} | Score: {score:.4f}")
        print(f"{'=' * 60}")

        # Imprime TODOS os metadados formatados bonitinhos
        print("📌 METADADOS:")
        print(json.dumps(node.metadata, indent=4, ensure_ascii=False))

        print("\n📝 TEXTO RECUPERADO:")
        print(node.text)


# ==========================================
# ÁREA DE TESTES
# ==========================================
if __name__ == "__main__":
    testar_query("Our mission?")
    # Teste a query que estava dando problema

    # Você pode adicionar outras queries para testar o comportamento do embedding
    # testar_query("Quais são as regras de férias?")
