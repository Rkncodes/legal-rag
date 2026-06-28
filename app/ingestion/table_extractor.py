"""
app/ingestion/table_extractor.py
---------------------------------
Digital-only table extraction using PyMuPDF's find_tables().
Called on demand via /tables/{pdf_name} endpoint.
Does NOT touch chunker, retriever, or ChromaDB.
"""

import fitz
from pathlib import Path


def extract_tables_from_pdf(pdf_path: str) -> list[dict]:
    """
    Extract all tables from a digital PDF using PyMuPDF find_tables().
    Returns a list of dicts: {page, table_index, headers, rows}
    """
    doc = fitz.open(pdf_path)
    results = []

    for page_num in range(len(doc)):
        page = doc[page_num]
        physical_page = page_num + 1

        try:
            tabs = page.find_tables()
        except Exception as e:
            print(f"[table_extractor] page {physical_page} error: {e}")
            continue

        if not tabs or not tabs.tables:
            continue

        for ti, table in enumerate(tabs.tables, start=1):
            try:
                raw_rows = table.extract()
            except Exception as e:
                print(f"[table_extractor] table extract error p{physical_page} t{ti}: {e}")
                continue

            if not raw_rows:
                continue

            # clean cells
            cleaned = []
            for row in raw_rows:
                cleaned_row = [(c or "").replace("\n", " ").strip() for c in row]
                cleaned.append(cleaned_row)

            # skip tables that are all empty
            flat = [cell for row in cleaned for cell in row]
            if not any(flat):
                continue

            # first row as headers if it looks like one
            headers = cleaned[0] if cleaned else []
            rows    = cleaned[1:] if len(cleaned) > 1 else []

            results.append({
                "page":        physical_page,
                "table_index": ti,
                "headers":     headers,
                "rows":        rows,
                "row_count":   len(rows),
                "col_count":   len(headers),
            })

    doc.close()
    print(f"[table_extractor] {Path(pdf_path).name} → {len(results)} tables found")
    return results