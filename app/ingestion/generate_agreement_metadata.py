from pathlib import Path
import json

from app.ingestion.pdf_loader import load_pdf


pdf_folder = Path("data/pdfs")

metadata = {}

for pdf_file in pdf_folder.rglob("*.pdf"):

    print(f"Processing {pdf_file.name}")

    pages = load_pdf(
        str(pdf_file)
    )

    first_pages_text = "\n".join(
        page["text"]
        for page in pages[:5]
    )

    metadata[pdf_file.name] = {
        "pdf_path": str(pdf_file),
        "metadata_text": first_pages_text
    }

with open(
    "agreement_metadata.json",
    "w",
    encoding="utf-8"
) as f:

    json.dump(
        metadata,
        f,
        indent=2,
        ensure_ascii=False
    )

print(
    f"Saved metadata for {len(metadata)} PDFs"
)