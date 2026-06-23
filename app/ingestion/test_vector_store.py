from pathlib import Path
import time
import json
import hashlib

from app.ingestion.pdf_loader import load_pdf
from app.ingestion.chunker import chunk_pages
from app.ingestion.vector_store import store_chunks
from app.ingestion import chunker

print(chunker.__file__)

pdf_folder = Path("data/pdfs")

PROCESSED_FILE = "processed_pdfs.json"


def get_pdf_hash(pdf_path):

    with open(pdf_path, "rb") as f:
        pdf_bytes = f.read()

    return hashlib.md5(
        pdf_bytes
    ).hexdigest()


try:

    with open(
        PROCESSED_FILE,
        "r"
    ) as f:

        processed_pdfs = set(
            json.load(f)
        )

except FileNotFoundError:

    processed_pdfs = set()

all_chunks = []

overall_start = time.time()

for pdf_file in pdf_folder.rglob("*.pdf"):

    pdf_hash = get_pdf_hash(
        pdf_file
    )
    

    if pdf_hash in processed_pdfs:

        print(
            f"\nSKIPPING: "
            f"{pdf_file.name}"
        )

        continue
    
    
    pdf_start = time.time()

    print(
        f"\n{'=' * 80}"
    )

    print(
        f"Loading: {pdf_file.name}"
    )

    print(
        f"{'=' * 80}"
    )

    pages = load_pdf(
        str(pdf_file)
    )

    print(
        f"\nPDF LOADING TIME: "
        f"{time.time() - pdf_start:.2f} seconds"
    )

    chunks = chunk_pages(
        pages
    )

    print(
        f"TOTAL PDF TIME "
        f"(LOAD + CHUNK): "
        f"{time.time() - pdf_start:.2f} seconds"
    )

    all_chunks.extend(
        chunks
    )
    
    processed_pdfs.add(
        pdf_hash
    )

print(
    f"\nTotal chunks collected: "
    f"{len(all_chunks)}"
)

if all_chunks:

    store_chunks(
        all_chunks
    )

else:

    print(
        "\nNo new PDFs to ingest."
    )

with open(
    PROCESSED_FILE,
    "w"
) as f:

    json.dump(
        list(processed_pdfs),
        f,
        indent=2
    )

print(
    f"\nTOTAL INGESTION TIME: "
    f"{time.time() - overall_start:.2f} seconds"
)