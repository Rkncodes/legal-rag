from langchain_text_splitters import RecursiveCharacterTextSplitter
import re


def split_into_sections(text):

    def looks_like_heading(line):

        words = line.split()

        if len(words) > 12:
            return False

        lower = line.lower()

        sentence_indicators = [
            "shall",
            "will",
            "may",
            "must",
            "should",
            "means",
            "includes",
            "include",
            "responsible",
            "required"
        ]

        if any(
           word in lower
        for word in sentence_indicators
    ):
         return False

        return True

    lines = text.split("\n")

    sections = []

    current_heading = None
    current_content = []

    numbered_heading_pattern = re.compile(
    r"^\d+(?:\.\d+)*\.?\s+[A-Z].+$"
)

    caps_heading_pattern = re.compile(
        r"^[A-Z][A-Z\s&\-]{3,}$"
    )

    article_heading_pattern = re.compile(
     r"^ARTICLE\s+\d+.*$",
     re.IGNORECASE
    )

    for line in lines:

        line = re.sub(
            r"^(\d+(?:\.\d+)+)([A-Z])",
            r"\1 \2",
            line
)

        line = line.strip()

        if not line:
            continue

        is_numbered_heading = (
            numbered_heading_pattern.match(line)
            and looks_like_heading(line)
        )

        is_caps_heading = (
           caps_heading_pattern.match(line)
        )

        is_article_heading = (
            article_heading_pattern.match(line)
        )

        if (
            is_numbered_heading
            or is_caps_heading
            or is_article_heading
               ):

            if current_heading:

                sections.append(
                    {
                        "heading": current_heading,
                        "content": "\n".join(current_content)
                    }
                )

            current_heading = line
            current_content = []

        else:

            current_content.append(line)

    if current_heading:

        sections.append(
            {
                "heading": current_heading,
                "content": "\n".join(current_content)
            }
        )

    return sections


def chunk_pages(pages):

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=2000,
        chunk_overlap=400
    )

    chunks = []

    document_id = pages[0]["pdf_name"]

    chunk_counter = 0

    for page in pages:

        sections = split_into_sections(
            page["text"]
        )

        if not sections:

            chunk_counter += 1

            chunks.append(
                {
                    "chunk_text": page["text"],
                    "heading": "",
                    "pdf_name": page["pdf_name"],
                    "page_number": page["page_number"],
                    "pdf_path": page["pdf_path"],
                    "document_id": document_id,
                    "chunk_id": chunk_counter,
                }
            )

            continue

        print(
            f"\nPAGE {page['page_number']} "
            f"SECTIONS FOUND: {len(sections)}"
        )

        for section in sections:

            heading = section["heading"]

            print("\nHEADING DETECTED:")
            print(repr(heading))

            print(
                f"SECTION -> {heading}"
            )

            section_text = (
                f"SECTION TITLE: {heading}\n\n"
                f"{section['content']}"
            )

            text_chunks = splitter.split_text(
                section_text
            )

            for chunk in text_chunks:

                chunk_counter += 1

                chunks.append(
                    {
                        "chunk_text": chunk,
                        "heading": heading,
                        "pdf_name": page["pdf_name"],
                        "page_number": page["page_number"],
                        "pdf_path": page["pdf_path"],
                        "document_id": document_id,
                        "chunk_id": chunk_counter,
                    }
                )

    print(
        f"\nTotal chunks created: {len(chunks)}"
    )

    return chunks