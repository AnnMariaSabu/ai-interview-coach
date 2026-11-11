"""
make_sample_files.py - Create Word and PDF versions of the fake resumes.
Run it once with: python make_sample_files.py
"""
from pathlib import Path

from docx import Document
from fpdf import FPDF

folder = Path("data/samples/resumes")

# Rahul's resume -> Word (.docx)
rahul_text = (folder / "rahul_data_analyst.txt").read_text(encoding="utf-8")
word_file = Document()
for line in rahul_text.split("\n"):
    word_file.add_paragraph(line)
word_file.save(folder / "rahul_data_analyst.docx")
print("Created rahul_data_analyst.docx")

# Priya's resume -> PDF
priya_text = (folder / "priya_ai_engineer.txt").read_text(encoding="utf-8")
pdf_file = FPDF()
pdf_file.add_page()
pdf_file.set_font("Helvetica", size=11)
pdf_file.multi_cell(0, 6, priya_text)
pdf_file.output(str(folder / "priya_ai_engineer.pdf"))
print("Created priya_ai_engineer.pdf")
