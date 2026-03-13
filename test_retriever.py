import os
from llama_index.core import (
    SimpleDirectoryReader,
    VectorStoreIndex,
    StorageContext,
    Settings,
    PromptTemplate,
)
from llama_index.core.node_parser import HierarchicalNodeParser, get_leaf_nodes
from llama_index.core.retrievers import AutoMergingRetriever
from llama_index.core.query_engine import RetrieverQueryEngine
from llama_index.core.storage.docstore import SimpleDocumentStore
from llama_index.vector_stores.qdrant import QdrantVectorStore
from llama_index.embeddings.ollama import OllamaEmbedding
from llama_index.llms.ollama import Ollama
import qdrant_client

from llama_index.postprocessor.sbert_rerank import SentenceTransformerRerank


def test_automerging_sbert(input_dir: str, query_text: str):
    print("1. Configurando LLM (ministral) e Embeddings (qwen3)...")
    Settings.embed_model = OllamaEmbedding(
        model_name="qwen3-embedding:8b", base_url="http://localhost:11434"
    )
    Settings.llm = Ollama(
        model="ministral-3:14b",
        base_url="http://localhost:11434",
        request_timeout=240.0,
    )

    print("2. Carregando documentos físicos...")
    documents = SimpleDirectoryReader(input_dir, required_exts=[".md"]).load_data()

    print("3. Fatiamento Hierárquico (Pai: 2048 tokens | Filho: 512 tokens)...")
    node_parser = HierarchicalNodeParser.from_defaults(chunk_sizes=[2048, 512])
    nodes = node_parser.get_nodes_from_documents(documents)

    leaf_nodes = get_leaf_nodes(nodes)

    print("4. Inicializando Qdrant e Document Store...")
    client = qdrant_client.QdrantClient(location=":memory:")
    vector_store = QdrantVectorStore(client=client, collection_name="test_sbert_rerank")

    docstore = SimpleDocumentStore()
    docstore.add_documents(nodes)

    storage_context = StorageContext.from_defaults(
        vector_store=vector_store, docstore=docstore
    )

    print("5. Indexando Nós Filhos...")
    index = VectorStoreIndex(leaf_nodes, storage_context=storage_context)

    print("6. Configurando AutoMergingRetriever e SBERT Reranker...")
    base_retriever = index.as_retriever(similarity_top_k=15)

    automerging_retriever = AutoMergingRetriever(
        base_retriever, storage_context, verbose=True
    )

    reranker = SentenceTransformerRerank(
        model="cross-encoder/ms-marco-MiniLM-L-6-v2", top_n=3
    )

    # AQUI ESTÁ A CORREÇÃO: Transformamos a string em um PromptTemplate
    qa_prompt = PromptTemplate(
        "Context information is below.\n"
        "---------------------\n{context_str}\n---------------------\n"
        "Given the context information and not prior knowledge, answer the query.\n"
        "Always cite the source document name from the context at the end of your answer.\n"
        "Query: {query_str}\nAnswer: "
    )

    query_engine = RetrieverQueryEngine.from_args(
        automerging_retriever,
        node_postprocessors=[reranker],
        text_qa_template=qa_prompt,  # <- Usando o objeto correto aqui
    )

    print(f"\n7. Gerando resposta final para: '{query_text}'")
    response = query_engine.query(query_text)

    print("\n=== RESPOSTA DO MINISTRAL-3 ===")
    print(response)
    print("===============================")


if __name__ == "__main__":
    MD_DIR = "data/Markdown"
    TEST_QUERY = "What are our core values? Please list all 5."
    test_automerging_sbert(MD_DIR, TEST_QUERY)
