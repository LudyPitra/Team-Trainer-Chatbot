import os
import redis
import qdrant_client
from dotenv import load_dotenv
from llama_index.core import StorageContext, VectorStoreIndex, Settings
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.llms.openai import OpenAI
from llama_index.vector_stores.qdrant import QdrantVectorStore
from llama_index.storage.docstore.redis import RedisDocumentStore
from llama_index.core.retrievers import AutoMergingRetriever, VectorIndexRetriever
from llama_index.core.postprocessor import LLMRerank
from llama_index.core.query_engine import RetrieverQueryEngine

load_dotenv()

Settings.embed_model = OpenAIEmbedding(model="text-embedding-3-small")
Settings.llm = OpenAI(model="gpt-4o-mini", temperature=0.1)


def get_rag_query_engine():
    """
    Builds and returns the advanced Query Engine (Auto-Merging + LLM Reranker).
    Can be used directly or as a Tool in an Agent.
    """

    print("Connecting to cloud databases...")

    debug = os.getenv("DEBUG", "False").lower() == "true"

    qdrant_url = os.environ["QDRANT_URL"]
    qdrant_api_key = os.environ["QDRANT_API_KEY"]
    redis_host = os.environ["REDIS_HOST"]
    redis_port = int(os.environ["REDIS_PORT"])
    redis_password = os.environ["REDIS_PASSWORD"]
    collection_name = "novamente_knowledge_base"

    client = qdrant_client.QdrantClient(url=qdrant_url, api_key=qdrant_api_key)
    vector_store = QdrantVectorStore(client=client, collection_name=collection_name)

    r_client = redis.Redis(
        host=redis_host,
        port=redis_port,
        password=redis_password,
        username="default",
        decode_responses=True,
    )

    docstore = RedisDocumentStore.from_redis_client(redis_client=r_client)

    storage_context = StorageContext.from_defaults(
        vector_store=vector_store, docstore=docstore
    )

    index = VectorStoreIndex.from_vector_store(
        vector_store=vector_store, storage_context=storage_context
    )

    base_retriever = VectorIndexRetriever(index=index, similarity_top_k=12)

    retriever = AutoMergingRetriever(
        vector_retriever=base_retriever,
        storage_context=storage_context,
        verbose=debug,  # Imprime no terminal quando o merge acontece!
    )

    reranker = LLMRerank(choice_batch_size=5, top_n=3, llm=OpenAI(model="gpt-4o-mini"))

    query_engine = RetrieverQueryEngine.from_args(
        retriever=retriever, node_postprocessors=[reranker]
    )

    return query_engine


if __name__ == "__main__":
    engine = get_rag_query_engine()
    print("RAG Query Engine is ready to use!")

    query = "What's our core values?"

    response = engine.query(query)

    print("\n--- RAG Query Response ---")
    print(response)
    print("\n--- Nodes used (after Rerank) ---")
    for node in response.source_nodes:
        print(f"- ID: {node.node.node_id} | Score: {node.score}")
