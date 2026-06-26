from sentence_transformers import CrossEncoder
from app.config import DEBUG

reranker = CrossEncoder(
    "BAAI/bge-reranker-base"
)


def rerank(query, retrieval_results):
    
    if not retrieval_results["documents"][0]:

     print(
        "\nNO DOCUMENTS TO RERANK\n"
    )

     return []

    chunks = retrieval_results["documents"][0]
    metadata = retrieval_results["metadatas"][0]

    pairs = []

    for chunk in chunks:
        pairs.append(
            [query, chunk]
        )

    scores = reranker.predict(pairs)

    if DEBUG:

        print("\nRERANKER DEBUG\n")

        for chunk, meta, score in zip(
            chunks,
            metadata,
            scores
        ):
            print(
                f"{meta['pdf_name']} | "
                f"Page {meta['page_number']} | "
                f"Score {float(score)}"
            )

    ranked = []

    for chunk, meta, score in zip(
        chunks,
        metadata,
        scores
    ):
        ranked.append(
            {
                "chunk": chunk,
                "metadata": meta,
                "score": float(score)
            }
        )

    ranked.sort(
        key=lambda x: x["score"],
        reverse=True
    )
    
    if not ranked:
        
        return []

    if DEBUG:

        print("\nAFTER SORTING\n")

        for i, item in enumerate(ranked[:10], start=1):

            print(
                f"{i}. "
                f"{item['metadata']['pdf_name']} | "
                f"Page {item['metadata']['page_number']} | "
                f"Score {item['score']}"
            )
            
    print("\nTOP CHUNK AFTER RERANKING\n")
    print(
        f"PDF: {ranked[0]['metadata']['pdf_name']} | "
        f"Page: {ranked[0]['metadata']['page_number']}"
    )
    print("-" * 80)
    print(ranked[0]["chunk"])
    print("-" * 80)
    
    print("\nRERANKER OUTPUT ORDER:")
    for i, item in enumerate(ranked[:5], start=1):
        print(f"  {i}. page={item['metadata']['page_number']} chunk_id={item['metadata'].get('chunk_id')} heading={item['metadata'].get('heading','')[:40]}")

    return ranked