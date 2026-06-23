from fastapi import FastAPI
from app.ingestion.reranker import rerank
from app.ingestion.retriever import retrieve
from app.llm.llm import generate_answer

from app.models import (
    QuestionRequest,
    QuestionResponse
)

app = FastAPI(
    title="Legal RAG API"
)



@app.get("/")
def root():
    return {
        "message": "Legal RAG API Running"
    }


@app.post(
    "/ask",
    response_model=QuestionResponse
)
def ask_question(request: QuestionRequest):

    print("\nASK ENDPOINT HIT\n")
    
    retrieval_results = retrieve(
        request.question,
        k=20
    )

    ranked_results = rerank(
        request.question,
        retrieval_results
    )
    
    if not ranked_results:

     return QuestionResponse(
        answer=
        "I don't know anything about that from the provided documents."
    )

    print("\n" + "=" * 80)
    print("TOP 5 AFTER RERANKING")
    print("=" * 80)

    for i, item in enumerate(ranked_results[:5], start=1):

        print(
            f"{i}. "
            f"Page {item['metadata']['page_number']} | "
            f"Score {item['score']}"
        )

        print(item["chunk"][:200])

        print("-" * 40)

    answer = generate_answer(
        request.question,
        ranked_results
    )

    return QuestionResponse(
        answer=answer
    )