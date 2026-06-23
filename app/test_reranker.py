from ingestion.retriever import retrieve
from ingestion.reranker import rerank

print("APP FILE RUNNING")

question = "What is the purpose of the agreement?"

results = retrieve(
    question,
    k=20
)

print("\nLOOKING FOR PURPOSE CHUNK\n")

for i, chunk in enumerate(results["documents"][0], start=1):

    if "1. PURPOSE" in chunk:

        print(f"FOUND AT RETRIEVAL POSITION {i}")

        print("\nCHUNK:\n")

        print(chunk)

        break

ranked = rerank(
    question,
    results
)

print("\nTOP 20 RERANKED RESULTS\n")

for i, item in enumerate(ranked[:20], start=1):

    print(
        i,
        "|",
        item["metadata"]["pdf_name"],
        "| Page",
        item["metadata"]["page_number"],
        "| Score",
        item["score"]
    )

print("\nSEARCHING FOR TESTFILE6 PAGE 3\n")

found = False

for i, item in enumerate(ranked, start=1):

    if (
        item["metadata"]["pdf_name"] == "testfile6.pdf"
        and item["metadata"]["page_number"] == 3
    ):

        found = True

        print(f"FOUND AT RERANK POSITION {i}")

        print(f"SCORE = {item['score']}")

        print("\nCHUNK:\n")

        print(item["chunk"])

        break

if not found:
    print("PAGE 3 NOT FOUND IN RERANKED RESULTS")