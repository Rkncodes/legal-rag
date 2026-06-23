from ingestion.retriever import retrieve
from llm.llm import generate_answer

question = input("Ask Question: ")

results = retrieve(question, k=5)

answer = generate_answer(
    question,
    results
)

print("\n")
print(answer)