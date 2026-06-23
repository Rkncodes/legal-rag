from app.ingestion.retriever import retrieve
from app.ingestion.reranker import rerank
print("HELLO FROM INGESTION TEST")

question = "What is the effective date of the agreement?"

results = retrieve(
    question,
    k=20
)

ranked = rerank(
    question,
    results
)

print("\nRANK 1 CHUNK:\n")
print(ranked[0]["chunk"])

print("\nRANK 2 CHUNK:\n")
print(ranked[1]["chunk"])

print("\nRANK 3 CHUNK:\n")
print(ranked[2]["chunk"])

print("\nRERANKED RESULTS\n")

for i, item in enumerate(ranked[:5], start=1):

    print(f"\nRank {i}")

    print(
        f"Score: {item['score']}"
    )

    print(
        f"PDF: {item['metadata']['pdf_name']}"
    )

    print(
        f"Page: {item['metadata']['page_number']}"
    )

    print("\nCHUNK:\n")

    print(
        item["chunk"][:800]
    )

    print("\n" + "-" * 80)
    
    print("\nTOP CHUNK PREVIEW\n")

print(
    ranked[0]["chunk"][:1000]
)

print("\nSECOND CHUNK PREVIEW\n")

print(
    ranked[1]["chunk"][:1000]
)