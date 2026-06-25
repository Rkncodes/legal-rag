from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.ingestion.reranker import rerank
from app.ingestion.retriever import retrieve
from app.llm.llm import generate_answer
from app.ingestion.retriever import collection
import re

from app.models import (
    QuestionRequest,
    QuestionResponse
)

app = FastAPI(
    title="Legal RAG API"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
    "http://localhost:5173",
    "http://127.0.0.1:5173"
],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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

@app.get("/keyword-search")
def keyword_search(
    keyword: str,
    agreement: str
):

    keyword = keyword.lower()

    results = collection.get(
        include=[
            "documents",
            "metadatas"
        ]
    )

    matches = []

    for doc, meta in zip(
        results["documents"],
        results["metadatas"]
    ):

        if agreement.lower() not in meta["pdf_name"].lower():
            continue

        doc_lower = doc.lower()

        if keyword not in doc_lower:
            continue

        index = doc_lower.find(keyword)

        start = max(
            0,
            index - 150
        )

        end = min(
            len(doc),
            index + 150
        )

        snippet = " ".join(
           doc[start:end].split()
        )

        snippet = re.sub(
            rf"(?i)({re.escape(keyword)})",
            r"<<<HIGHLIGHT>>>\1<<<END>>>",
            snippet
        )

        matches.append(
            {
                "page_number":
                    meta["page_number"],

                "heading":
                    meta.get(
                        "heading",
                        ""
                    ),

                "snippet":
                    snippet
            }
        )

    return {
        "keyword": keyword,
        "agreement": agreement,
        "count": len(matches),
        "matches": matches
    }

@app.get("/agreements")
def get_agreements():

    results = collection.get(
        include=["metadatas"]
    )

    agreements = set()

    for meta in results["metadatas"]:

        agreements.add(
            meta["pdf_name"]
        )

    return {
        "agreements": sorted(
            list(agreements)
        )
    }