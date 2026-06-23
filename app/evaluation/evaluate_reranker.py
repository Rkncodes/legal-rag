from app.ingestion.retriever import retrieve
from app.ingestion.reranker import rerank
from app.evaluation.qa_test_cases import test_cases

total = len(test_cases)

top1 = 0
top3 = 0
top5 = 0

for case in test_cases:

    question = case["question"]
    expected_pdf = case["pdf"]
    expected_page = case["page"]

    retrieval_results = retrieve(
        question,
        k=20
    )

    ranked_results = rerank(
        question,
        retrieval_results
    )

    found_rank = None

    for i, item in enumerate(
        ranked_results,
        start=1
    ):

        metadata = item["metadata"]

        if (
            metadata["pdf_name"] == expected_pdf
            and
            metadata["page_number"] == expected_page
        ):
            found_rank = i
            break

    print("\n" + "=" * 60)

    print("Question:", question)

    print(
        "Expected:",
        expected_pdf,
        "Page",
        expected_page
    )

    print("Reranked Rank:", found_rank)
    
    print(
    "Top Reranked Result:",
    ranked_results[0]["metadata"]["pdf_name"],
    "Page",
    ranked_results[0]["metadata"]["page_number"],
    "| Score:",
    ranked_results[0]["score"]
    )

    if found_rank:
     print(
        "Correct Page Score:",
        ranked_results[found_rank - 1]["score"]
    )

    # print("\nTop 5 Reranked Results:")

    # for item in ranked_results[:5]:

    #  print(
    #     f"{item['metadata']['pdf_name']} | "
    #     f"Page {item['metadata']['page_number']} | "
    #     f"Score {item['score']}"
    # )

    else:

     print(
        "\nCorrect page not found in reranked results."
    )

    if found_rank == 1:
     top1 += 1

    if found_rank and found_rank <= 3:
     top3 += 1

    if found_rank and found_rank <= 5:
     top5 += 1


print("\n" + "=" * 60)
print("FINAL RERANKER RESULTS")

print(
    f"Top-1 Recall: {(top1/total)*100:.2f}%"
)

print(
    f"Top-3 Recall: {(top3/total)*100:.2f}%"
)

print(
    f"Top-5 Recall: {(top5/total)*100:.2f}%"
)

not_found = total - top5

print(
    f"\nQuestions missed entirely: {not_found}"
)