from pathlib import Path

from docx import Document


def read_paragraphs(docx_path: Path) -> list[str]:
    document = Document(str(docx_path))
    return [paragraph.text for paragraph in document.paragraphs]

