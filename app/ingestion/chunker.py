from langchain_text_splitters import RecursiveCharacterTextSplitter
import re

def extract_section_id(heading):

    if not heading:
        return None

    heading = heading.strip()

    # Numbered headings
    m = re.match(r"^(\d+)(?:\.(\d+))?", heading)
    if m:
        if m.group(2):
            return f"{m.group(1)}.{m.group(2)}"
        return m.group(1)

    # PART headings
    m = re.match(r"^PART\s+([IVXLCDM]+)", heading, re.IGNORECASE)
    if m:
        return f"PART_{m.group(1).upper()}"

    # ARTICLE headings
    m = re.match(r"^ARTICLE\s+(\d+)", heading, re.IGNORECASE)
    if m:
        return f"ARTICLE_{m.group(1)}"

    # Generic CAPS headings
    words = re.findall(r"[A-Z]+", heading.upper())
    if words:
        return "_".join(words[:3])

    return None

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

        if any(word in lower for word in sentence_indicators):
            return False

        return True

    def normalize_heading(line):
        """Normalize OCR misreads of Roman numerals without hardcoding text."""
        line = re.sub(r'\bPART\s+111\b', 'PART III', line, flags=re.IGNORECASE)
        line = re.sub(r'\bPART\s+11\b',  'PART II',  line, flags=re.IGNORECASE)
        line = re.sub(r'\bPART\s+1V\b',  'PART IV',  line, flags=re.IGNORECASE)
        line = re.sub(r'\bPART\s+V11\b', 'PART VII', line, flags=re.IGNORECASE)
        line = re.sub(r'\bPART\s+V1\b',  'PART VI',  line, flags=re.IGNORECASE)
        return line

    lines = text.split("\n")
    
    merged = []

    i = 0

    while i < len(lines):

        current = lines[i].strip()

        if (
            re.fullmatch(r"\d+\.?", current)
            and i + 1 < len(lines)
        ):
           nxt = lines[i + 1].strip()

           if nxt and len(nxt.split()) <= 12:
               merged.append(current + " " + nxt)
               i += 2
               continue

        merged.append(current)
        i += 1

    lines = merged

    sections          = []
    current_heading   = None
    current_content   = []
    current_page      = 1
    current_heading_page = 1
    current_content_page = None

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

    part_heading_pattern = re.compile(
        r"^PART\s+[IVXLCDM0-9]+[\s:\-]+.{0,60}$",
        re.IGNORECASE
    )

    page_marker_pattern = re.compile(
        r"^<<<PAGE_(\d+)>>>$"
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

        # track page number from marker
        page_match = page_marker_pattern.match(line)
        if page_match:
            current_page = int(page_match.group(1))
            continue

        is_numbered_heading = (
            numbered_heading_pattern.match(line)
            and looks_like_heading(line)
        )

        is_caps_heading = (
           bool(caps_heading_pattern.match(line))
           and len(line.split()) <= 8
           and "MASTER SERVICE AGREEMENT" not in line.upper()
        )
        is_article_heading = bool(article_heading_pattern.match(line))
        is_part_heading    = bool(part_heading_pattern.match(line))

        if (
            is_numbered_heading
            or is_caps_heading
            or is_article_heading
            or is_part_heading
        ):
            # save previous section always — even if content is empty
            # empty content sections are valid parent headings (e.g. PART IV)
            # whose sub-sections will be found via section_id expansion
            if current_heading:
                sections.append({
                    "heading":     current_heading,
                    "content":     "\n".join(current_content),
                    "page_number": current_content_page or current_heading_page,
                    "section_id":  extract_section_id(current_heading),
                })

            normalized           = normalize_heading(line)
            current_heading      = normalized
            current_content      = []
            current_heading_page = current_page
            current_content_page = None

        else:
            if current_content_page is None:
                current_content_page = current_page
            current_content.append(line)

    # save last section always
    if current_heading:
        sections.append({
            "heading":     current_heading,
            "content":     "\n".join(current_content),
            "page_number": current_content_page or current_heading_page,
            "section_id":  extract_section_id(current_heading),
        })

    return sections


def chunk_pages(pages):

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=2200,
        chunk_overlap=500
    )

    chunks = []

    document_id = pages[0]["pdf_name"]
    pdf_name    = pages[0]["pdf_name"]
    pdf_path    = pages[0]["pdf_path"]

    chunk_counter = 0

    # merge all pages into one text stream
    merged_lines = []

    for page in pages:
        merged_lines.append(f"<<<PAGE_{page['page_number']}>>>")
        merged_lines.append(page["text"])

    merged_text = "\n".join(merged_lines)

    # split merged text into sections
    sections = split_into_sections(merged_text)

    print(f"\nDOCUMENT: {pdf_name}\nTOTAL SECTIONS FOUND: {len(sections)}")

    if not sections:
        for page in pages:
            chunk_counter += 1
            chunks.append({
                "chunk_text":  page["text"],
                "heading":     "",
                "section_id":  None,
                "pdf_name":    pdf_name,
                "page_number": page["page_number"],
                "pdf_path":    pdf_path,
                "document_id": document_id,
                "chunk_id":    chunk_counter,
            })
        return chunks

    # chunk each section
    for section in sections:

        heading     = section["heading"]
        page_number = section["page_number"]
        section_id  = section["section_id"]

        print(f"SECTION: {heading} | Page: {page_number} | SectionID: {section_id}")

        section_text = (
            f"SECTION TITLE: {heading}\n\n"
            f"{section['content']}"
        )

        text_chunks = splitter.split_text(section_text)

        for chunk in text_chunks:
            chunk_counter += 1
            # extract the actual page number from the chunk text if present
            
            chunks.append({
                "chunk_text":  chunk,
                "heading":     heading,
                "section_id":  section_id,
                "pdf_name":    pdf_name,
                "page_number": page_number,
                "pdf_path":    pdf_path,
                "document_id": document_id,
                "chunk_id":    chunk_counter,
            })

    print(f"\nTotal chunks created: {len(chunks)}")

    return chunks