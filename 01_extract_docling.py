from pathlib import Path
from docling.document_converter import DocumentConverter


def convert_pdfs(input_dir: str, output_dir: str):
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    pdf_files = list(input_path.glob("*.pdf"))
    print(f"{len(pdf_files)} PDF files found in '{input_dir}'")

    converter = DocumentConverter()

    for pdf in pdf_files:
        print(f"Converting: {pdf}")

        try:
            result = converter.convert(str(pdf))

            md_text = result.document.export_to_markdown()
            output_file = output_path / f"{pdf.stem}.md"
            output_file.write_text(md_text, encoding="utf-8")

            print(f" -> Success! Saved in: {output_file}")
        except Exception as e:
            print(f" -> Error to convert {pdf.name}: {e}")


if __name__ == "__main__":
    INPUT_DIR = "data/PDFs"
    OUTPUT_DIR = "data/Markdown"

    convert_pdfs(INPUT_DIR, OUTPUT_DIR)
    print("\nExtração da Fase 1 concluída!")
