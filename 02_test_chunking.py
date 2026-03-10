from llama_index.core import SimpleDirectoryReader
from llama_index.core.node_parser import MarkdownNodeParser


def test_markdown_chunking(input_dir: str):
    print(f"Loading markdown files from: {input_dir}")

    documents = SimpleDirectoryReader(input_dir, required_exts=[".md"]).load_data()
    print(f"{len(documents)} documents loaded.\n")

    print("Starting chunking with MarkdownNodeParser...")
    parser = MarkdownNodeParser()
    nodes = parser.get_nodes_from_documents(documents)

    print(f"Total of genereted chunks: {len(nodes)}\n")

    if nodes:
        first_node = nodes[0]
        print("=== INSPEÇÃO DO PRIMEIRO NODE ===")
        print(f"Nome do ficheiro original: {first_node.metadata.get('file_name')}")
        print(f"Tamanho do chunk (carateres): {len(first_node.text)}")
        print("-" * 40)
        # Mostramos os primeiros 500 carateres para ter uma ideia
        print(first_node.text[:500] + "...\n[TEXTO TRUNCADO]")
        print("=================================")


if __name__ == "__main__":
    MD_DIR = "data/Markdown"

    test_markdown_chunking(MD_DIR)
