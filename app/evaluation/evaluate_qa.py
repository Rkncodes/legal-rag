from app.evaluation.qa_test_cases import test_cases

from app.ingestion.retriever import retrieve
from app.ingestion.reranker import rerank

from app.llm.llm import generate_answer


passed = 0
total = len(test_cases)

for case in test_cases:

    question = case["question"]
    expected = case["expected_answer"]

    retrieval_results = retrieve(
        question,
        k=20
    )

    ranked_results = rerank(
        question,
        retrieval_results
    )

    answer = generate_answer(
        question,
        ranked_results
    )

    answer_lower = answer.lower()
    expected_lower = expected.lower()

    success = expected_lower in answer_lower

    if success:
        passed += 1

    print("\n" + "=" * 80)

    print("QUESTION:")
    print(question)

    print("\nEXPECTED:")
    print(expected)

    print("\nACTUAL:")
    print(answer)

    print("\nRESULT:")
    print("PASS" if success else "FAIL")

print("\n" + "=" * 80)

print("FINAL QA RESULTS")

print(f"Passed: {passed}/{total}")

print(
    f"QA Accuracy: {(passed/total)*100:.2f}%"
)