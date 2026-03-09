from llama_index.readers.docling import DoclingReader
from llama_index.core.node_parser import MarkdownNodeParser
from llama_index.core import SimpleDirectoryReader

# Caminho para os PDFs do seu projeto
SOURCE = "/home/ludy-dev/Documents/02-Projects/LLM-for-company-teams/data/PDFs/"


def debug_metadata_extraction():
    print("⏳ Inicializando DoclingReader...")
    reader = DoclingReader()

    # Carregamos apenas o diretório
    dir_reader = SimpleDirectoryReader(
        input_dir=SOURCE,
        required_exts=[".pdf"],
        file_extractor={".pdf": reader},
        recursive=False,
        num_files_limit=1,  # ATENÇÃO: Limitamos a 1 arquivo para não inundar o terminal
    )

    print("⏳ Lendo o primeiro PDF (isso pode demorar uns segundos)...")
    documents = dir_reader.load_data()
    print("LOOK HERE")
    print(documents)
    print("\n=========\n")

    if not documents:
        print("❌ Nenhum documento encontrado!")
        return

    doc = documents[0]
    file_name = doc.metadata.get("file_name", "Desconhecido")

    print("\n" + "=" * 60)
    print(f"📄 ARQUIVO EM ANÁLISE: {file_name}")
    print("=" * 60)

    # FASE 1: O TESTE DO DOCLING
    # Vamos ver se o Markdown gerado faz sentido ou se está uma bagunça
    print("\n👀 FASE 1: O que o Docling gerou (Primeiros 1000 caracteres):")
    print("-" * 60)
    print(doc.text[:1000] + "\n\n[... TEXTO CORTADO PARA O DEBUG ...]")
    print("-" * 60)

    # FASE 2: O TESTE DO PARSER
    print("\n⏳ Passando o texto pelo MarkdownNodeParser...")
    node_parser = MarkdownNodeParser()
    nodes = node_parser.get_nodes_from_documents([doc])
    print("LOOK HERE")
    print(nodes)
    print("\n=========\n")
    print(f"✅ O parser dividiu o documento em {len(nodes)} blocos (nodes).")

    print("\n👀 FASE 2: Inspecionando os 3 primeiros blocos gerados:")
    print("=" * 60)

    for i, node in enumerate(nodes[:3]):
        print(f"\n📦 BLOCO {i + 1}:")
        print(f"📝 TEXTO (Primeiros 100 chars): {node.text[:100].strip()}...")

        # Extraindo os metadados chave para o nosso RAG
        header_path = node.metadata.get("header_path", "NÃO ENCONTRADO")
        page_label = node.metadata.get("page_label", "SEM PÁGINA")

        print(f"🏷️  METADADOS COMPLETOS: {node.metadata}")
        print(f"📍 HEADER PATH GERADO: {header_path}")
        print(f"📄 PÁGINA: {page_label}")
        print("-" * 60)


if __name__ == "__main__":
    debug_metadata_extraction()
