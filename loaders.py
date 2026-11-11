"""
loaders.py - Read resumes and job descriptions from files.
Supports .txt, .pdf and .docx files.
"""
import re
from pathlib import Path

from docx import Document
from pypdf import PdfReader


def load_txt(path: Path) -> str:
    """Read a plain text file."""
    return path.read_text(encoding="utf-8")


def load_pdf(path: Path) -> str:
    """Read the text from every page of a PDF file."""
    reader = PdfReader(path)
    pages = [page.extract_text() or "" for page in reader.pages]
    return "\n".join(pages)


def load_docx(path: Path) -> str:
    """Read the text from every paragraph of a Word file."""
    document = Document(path)
    paragraphs = [paragraph.text for paragraph in document.paragraphs]
    return "\n".join(paragraphs)


def load_document(file_path: str) -> str:
    """Look at the file type and use the right reader."""
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    file_type = path.suffix.lower()

    if file_type == ".txt":
        return load_txt(path)
    if file_type == ".pdf":
        return load_pdf(path)
    if file_type == ".docx":
        return load_docx(path)

    raise ValueError(f"Unsupported file type: {file_type}. Please use .txt, .pdf or .docx")


def clean_text(text: str) -> str:
    """Tidy up messy text so the AI can read it easily."""
    # 1. Use the same line ending everywhere
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    # 2. Replace odd characters
    text = text.replace("\u00a0", " ")  # invisible "non-breaking" space
    text = text.replace("\t", " ")      # tab
    text = text.replace("\u2022", "-")  # bullet point •

    # 3. Many spaces in a row -> one space
    text = re.sub(r" {2,}", " ", text)

    # 4. Remove spaces at the start and end of every line
    lines = [line.strip() for line in text.split("\n")]
    text = "\n".join(lines)

    # 5. Many empty lines in a row -> one empty line
    text = re.sub(r"\n{3,}", "\n\n", text)

    # 6. Remove empty space at the very start and end
    return text.strip()


def read_document(file_path: str) -> str:
    """Load any supported file and return clean text."""
    return clean_text(load_document(file_path))