import os
from pathlib import Path
from llama_index.core import SimpleDirectoryReader
from llama_index.core.readers.base import BaseReader
from llama_index.readers.docling import DoclingReader

SOURCE_DIR = "data/PDFs"
MARKDOWN_DIR = "data/Markdown"
SUPPORTED_EXTS = {".pdf", ".docx", ".md", ".csv", ".txt"}


def setup_directories():
    """Ensures that the input and output folders exist before starting."""

    if not os.path.exists(SOURCE_DIR):
        print(f"❌ Error: Source directory not found: {SOURCE_DIR}")
        return False

    Path(MARKDOWN_DIR).mkdir(parents=True, exist_ok=True)
    print(f"📁 Output directory checked/created: {MARKDOWN_DIR}")

    return True


def convert_files():
    """Read the files from the source directory and convert them to markdown format."""

    print("⏳Starting file conversion...(it can take a few seconds in the first time)")
    docling_reader = DoclingReader()

    file_extractor: dict[str, BaseReader] = {
        ext: docling_reader for ext in SUPPORTED_EXTS
    }

    processed_files = 0

    for filename in os.listdir(SOURCE_DIR):
        file_path = os.path.join(SOURCE_DIR, filename)

        if os.path.isdir(file_path):
            continue

        ext = os.path.splitext(filename)[1].lower()

        if ext not in SUPPORTED_EXTS:
            print(f"⚠️ Skipping unsupported file type: {filename}")
            continue

        print(f"Processing: {filename}...")

        try:
            reader = SimpleDirectoryReader(
                input_files=[file_path],
                file_extractor=file_extractor,
            )

            documents = reader.load_data()

            full_text = "\n\n".join(doc.text for doc in documents)

            base_name = os.path.splitext(filename)[0]
            output_filename = f"{base_name}.md"
            output_path = os.path.join(MARKDOWN_DIR, output_filename)

            with open(output_path, "w", encoding="utf-8") as f:
                f.write(full_text)

            print(f"✅ Saved: {output_filename}")
            processed_files += 1

        except Exception as e:
            print(f"❌ Error processing {filename}: {e}")

    print(
        f"🎉 Done! {processed_files} files successfully converted to the {MARKDOWN_DIR} folder."
    )


if __name__ == "__main__":
    if setup_directories():
        convert_files()
