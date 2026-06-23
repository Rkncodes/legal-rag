from pathlib import Path

import fitz
import pytesseract
from PIL import Image
import json
import hashlib

pytesseract.pytesseract.tesseract_cmd = (
    r"C:\Users\Rajvinder.kaur\AppData\Local\Programs\Tesseract-OCR\tesseract.exe"
)

CACHE_DIR = "cache"
OCR_CACHE_VERSION = "v1"


def preprocess_for_ocr(img):

    img = img.convert("L")

    img = img.point(
        lambda x: 0 if x < 160 else 255,
        mode="1"
    )

    return img


def extract_page_text(page):
    """
    Try normal text extraction first.
    If no text is found, fall back to OCR.
    """

    text = page.get_text().strip()

    if text:
        return text

    print(
        f"OCR triggered on page "
        f"{page.number + 1}"
    )

    pix = page.get_pixmap(
        matrix=fitz.Matrix(8, 8)
    )

    image_path = "temp_page.png"

    pix.save(image_path)

    img = Image.open(
        image_path
    )

    # img = preprocess_for_ocr(img)

    text = pytesseract.image_to_string(
        img,
        lang="eng",
        config="--oem 3 --psm 4"
    )

    return text.strip()


def classify_pdf(doc):

    sample_size = min(
        3,
        len(doc)
    )

    text_pages = 0

    for i in range(sample_size):

        text = doc[i].get_text().strip()

        if len(text) > 50:
            text_pages += 1

    if text_pages == sample_size:
        return "digital"

    if text_pages == 0:
        return "scanned"

    return "mixed"


def get_pdf_hash(pdf_path):

    with open(
        pdf_path,
        "rb"
    ) as f:

        pdf_bytes = f.read()

    return hashlib.md5(
        pdf_bytes +
        OCR_CACHE_VERSION.encode()
    ).hexdigest()


def get_cache_file(pdf_path):

    pdf_hash = get_pdf_hash(
        pdf_path
    )
    

    return (
        f"{CACHE_DIR}/{pdf_hash}.json"
    )


def load_pdf(pdf_path):

    doc = fitz.open(
        pdf_path
    )

    cache_file = get_cache_file(
        pdf_path
    )

    try:

        with open(
            cache_file,
            "r",
            encoding="utf-8"
        ) as f:

            cached_pages = json.load(f)

        print(
            "\nCACHE HIT ->",
            Path(pdf_path).name
        )

        doc.close()

        return cached_pages

    except FileNotFoundError:

        print(
            "\nCACHE MISS ->",
            Path(pdf_path).name
        )

    pdf_type = classify_pdf(
        doc
    )

    print(
        f"\nPDF TYPE DETECTED: "
        f"{pdf_type.upper()}"
    )

    pages = []

    for page_num in range(len(doc)):

        page = doc[page_num]

        # DIGITAL PDF
        if pdf_type == "digital":

            text = page.get_text().strip()

        # SCANNED PDF
        elif pdf_type == "scanned":

            print(
                f"OCR triggered on page "
                f"{page_num + 1}"
            )

            pix = page.get_pixmap(
                matrix=fitz.Matrix(8, 8)
            )

            image_path = "temp_page.png"

            pix.save(
                image_path
            )

            img = Image.open(
                image_path
            )

            text = pytesseract.image_to_string(
                img,
                lang="eng",
                config="--oem 3 --psm 4"
            ).strip()

        # MIXED PDF
        else:

            text = extract_page_text(
                page
            )

        pages.append(
            {
                "pdf_name": Path(pdf_path).name,
                "page_number": page_num + 1,
                "pdf_path": pdf_path,
                "text": text,
            }
        )

    Path(
        CACHE_DIR
    ).mkdir(
        exist_ok=True
    )

    with open(
        cache_file,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            pages,
            f,
            ensure_ascii=False,
            indent=2
        )

    print(
        "\nCACHE SAVED ->",
        Path(pdf_path).name
    )

    doc.close()

    return pages