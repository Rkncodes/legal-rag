# app/test_chunker.py

from app.ingestion.pdf_loader import load_pdf
from app.ingestion.chunker import chunk_pages

pages = load_pdf(
    "data/pdfs/AIRTEL/AIRTEL2.pdf"
)

chunks = chunk_pages(pages)

print("\nTOTAL CHUNKS:", len(chunks))