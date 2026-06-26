import chromadb
import re
from sentence_transformers import SentenceTransformer
from app.config import DEBUG
from app.ingestion.agreement_detector import detect_agreement

try:
    from rank_bm25 import BM25Okapi
    BM25_AVAILABLE = True
except ImportError:
    BM25_AVAILABLE = False
    print("rank_bm25 not installed — BM25 disabled. Run: pip install rank-bm25")

embedding_model = SentenceTransformer("BAAI/bge-small-en-v1.5")

client = chromadb.PersistentClient(path="chroma_db")

collection = client.get_collection("legal_documents")

print("Collection count:", collection.count())


def get_neighbor_chunks(metadata):

    pdf_name = metadata["pdf_name"]
    chunk_id = metadata["chunk_id"]

    neighbors = collection.get(
        where={"pdf_name": pdf_name},
        include=["documents", "metadatas"]
    )

    expanded = []

    for doc, meta in zip(neighbors["documents"], neighbors["metadatas"]):
        if abs(int(meta["chunk_id"]) - int(chunk_id)) <= 3:
            expanded.append((doc, meta))

    return expanded


def get_section_chunks(metadata):
    """Fetch ALL chunks with the same section_id from the same PDF.
    This pulls the complete clause family — e.g. all of section 6
    (6.1, 6.1.1, 6.2, 6.3, 6.4, 6.4.1 ... 6.4.5).
    """
    section_id = metadata.get("section_id", "")
    pdf_name   = metadata["pdf_name"]

    if not section_id:
        return get_neighbor_chunks(metadata)

    results = collection.get(
        where={
            "$and": [
                {"pdf_name":   {"$eq": pdf_name}},
                {"section_id": {"$eq": section_id}},
            ]
        },
        include=["documents", "metadatas"]
    )

    if not results["documents"]:
        return get_neighbor_chunks(metadata)

    return list(zip(results["documents"], results["metadatas"]))


def normalize_query(query):
    query = query.lower()
    query = query.replace("master service agreement", "")
    query = query.replace("master services agreement", "")
    query = query.replace("msa", "")
    query = query.replace("what is the clause for", "")
    query = query.replace("what is", "")
    return query.strip()


def tokenize(text):
    """Simple tokenizer for BM25."""
    return re.findall(r"[a-z0-9]+", text.lower())


def retrieve(query, k=15, force_agreement=None):

    print("\nQUERY RECEIVED:", query)

    query_for_search = normalize_query(query)

    print("NORMALIZED QUERY:", query_for_search)

    query_embedding = embedding_model.encode(
        query_for_search,
        normalize_embeddings=True
    ).tolist()

    where_filter = None

    if force_agreement:
        where_filter = {"pdf_name": force_agreement}
        agreement_pdf = force_agreement
        print(f"\nFORCE AGREEMENT: {force_agreement}")
    else:
        agreement_pdf = detect_agreement(query, collection)
        if agreement_pdf:
            where_filter = {"pdf_name": agreement_pdf}
            print(f"\nAGREEMENT DETECTED: {agreement_pdf}")

    print(f"\nWHERE FILTER: {where_filter}")

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=80,
        where=where_filter,
        include=["documents", "metadatas", "distances"]
    )

    if not results["metadatas"][0]:
        print("\nNO RESULTS FOUND FOR FILTER\n")
        return {"documents": [[]], "metadatas": [[]], "distances": [[]]}

    documents = results["documents"][0]
    metadatas = results["metadatas"][0]
    distances = results["distances"][0]

    print("\nRAW RETRIEVAL RESULTS\n")
    for rank, (doc, meta, dist) in enumerate(
        zip(documents, metadatas, distances), start=1
    ):
        print(
            f"{rank}. {meta['pdf_name']} | "
            f"Page {meta['page_number']} | "
            f"Distance {dist}"
        )

    # ── BM25 scoring ──────────────────────────────────────────────────
    bm25_scores = {}
    if BM25_AVAILABLE and documents:
        corpus = [tokenize(doc) for doc in documents]
        bm25   = BM25Okapi(corpus)
        query_tokens = tokenize(query_for_search)
        scores = bm25.get_scores(query_tokens)
        # normalize BM25 scores to 0-1
        max_bm25 = max(scores) if max(scores) > 0 else 1
        for i, score in enumerate(scores):
            bm25_scores[i] = score / max_bm25

    # ── boosting ──────────────────────────────────────────────────────
    boosted = []

    for idx, (doc, meta, dist) in enumerate(zip(documents, metadatas, distances)):

        # semantic score
        score = -dist

        # BM25 boost
        if BM25_AVAILABLE and idx in bm25_scores:
            score += bm25_scores[idx] * 0.3
            
        pdf_name    = meta.get("pdf_name", "").lower()
        query_lower = query.lower()

        if pdf_name in query_lower:
            score += 20
            print(f"PDF BOOST APPLIED -> {pdf_name}")

        heading = meta.get("heading", "").lower()
        clean_heading = re.sub(r"^\d+(\.\d+)*\s*", "", heading).strip()

        if clean_heading:
            query_words   = set(query_lower.split())
            heading_words = set(clean_heading.split())
            overlap       = len(query_words & heading_words)

            if query_lower in clean_heading or clean_heading in query_lower:
                score += 25
                print(f"EXACT HEADING BOOST -> {heading}")
            elif overlap >= 3:
                score += 10
                print(f"PARTIAL HEADING BOOST -> {heading}")

        boosted.append((score, doc, meta, dist))

    boosted.sort(reverse=True, key=lambda x: x[0])

    print("\nTOP 10 AFTER BOOSTING\n")
    for i, item in enumerate(boosted[:10], start=1):
        print(
            f"{i}. {item[2]['pdf_name']} | "
            f"Page {item[2]['page_number']} | "
            f"SectionID: {item[2].get('section_id','')} | "
            f"Heading: {item[2].get('heading','')[:50]}"
        )

    # ── section expansion (replaces brittle neighbor ±3) ─────────────
    expanded_docs = []
    expanded_meta = []
    seen = set()

    for item in boosted[:5]:
        _, _, meta, _ = item

        # use section expansion if section_id exists, else neighbor
        section_chunks = get_section_chunks(meta)

        for doc, neighbor_meta in section_chunks:
            key = (neighbor_meta["pdf_name"], neighbor_meta["chunk_id"])
            if key in seen:
                continue
            seen.add(key)
            expanded_docs.append(doc)
            expanded_meta.append(neighbor_meta)

    # also expand neighbors for top 3 to catch cross-section continuations
    for item in boosted[:3]:
        _, _, meta, _ = item
        neighbors = get_neighbor_chunks(meta)
        for doc, neighbor_meta in neighbors:
            key = (neighbor_meta["pdf_name"], neighbor_meta["chunk_id"])
            if key in seen:
                continue
            seen.add(key)
            expanded_docs.append(doc)
            expanded_meta.append(neighbor_meta)

    results["documents"][0] = expanded_docs
    results["metadatas"][0] = expanded_meta
    results["distances"][0] = [0 for _ in expanded_docs]

    pages = sorted(set(m["page_number"] for m in expanded_meta))
    print(f"\nPAGES RETURNED: {pages}")

    if DEBUG:
        print("\n" + "=" * 80)
        print(f"QUERY: {query}")
        print("=" * 80)
        print("\nBOOSTED RESULTS\n")

        for i in range(len(results["documents"][0])):
            metadata = results["metadatas"][0][i]
            document = results["documents"][0][i]
            print(f"\nRank {i + 1}")
            print(f"PDF: {metadata['pdf_name']}")
            print(f"Page: {metadata['page_number']}")
            if "heading" in metadata:
                print(f"Heading: {metadata['heading']}")
            if "chunk_id" in metadata:
                print(f"Chunk ID: {metadata['chunk_id']}")
            print("\nTEXT PREVIEW:")
            print("-" * 40)
            print(document[:500])
            print("-" * 40)

    return results