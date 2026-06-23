from app.ingestion.retriever import retrieve
from app.evaluation.qa_test_cases import test_cases

total = len(test_cases)

top1 = 0
top5 = 0
top10 = 0
top20 = 0

failed_questions = []

for case in test_cases:

    question = case["question"]
    expected_pdf = case["pdf"]
    expected_page = case["page"]

    results = retrieve(
        question,
        k=20
    )

    found_rank = None

    for i, metadata in enumerate(
        results["metadatas"][0],
        start=1
    ):

        if (
            metadata["pdf_name"] == expected_pdf
            and
            metadata["page_number"] == expected_page
        ):
            found_rank = i
            break

    if not found_rank or found_rank > 5:

        failed_questions.append(question)

        print("\n" + "=" * 60)

        print("FAILED QUESTION:")
        print(question)

        print(
            "Expected:",
            expected_pdf,
            "Page",
            expected_page
        )

        print("Retrieved Rank:", found_rank)

        top_metadata = results["metadatas"][0][0]

        print(
            "Top Retrieved Result:",
            top_metadata["pdf_name"],
            "Page",
            top_metadata["page_number"]
        )
        
    for i, metadata in enumerate(
    results["metadatas"][0][:5],
    start=1
    ):
     print(
        f"Rank {i}:",
        metadata["pdf_name"],
        "Page",
        metadata["page_number"]
    )

    if found_rank == 1:
        top1 += 1

    if found_rank and found_rank <= 5:
        top5 += 1

    if found_rank and found_rank <= 10:
        top10 += 1

    if found_rank and found_rank <= 20:
        top20 += 1

print("\n" + "=" * 60)

print("FINAL RESULTS")

print(
    f"Top-1 Recall: {(top1 / total) * 100:.2f}%"
)

print(
    f"Top-5 Recall: {(top5 / total) * 100:.2f}%"
)

print(
    f"Top-10 Recall: {(top10 / total) * 100:.2f}%"
)

print(
    f"Top-20 Recall: {(top20 / total) * 100:.2f}%"
)

print("\nFAILED QUESTIONS:")

for q in failed_questions:
    print("-", q)