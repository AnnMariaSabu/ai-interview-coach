"""
check_loaders.py - Quick check: read every sample file and show a preview.
Run it with: python check_loaders.py
"""
from pathlib import Path

from loaders import read_document

for file in sorted(Path("data/samples").rglob("*")):
    if file.is_file():
        text = read_document(str(file))
        first_line = text.split("\n")[0]
        print(f"OK  {file.name:28} {len(text):5} characters | {first_line}")