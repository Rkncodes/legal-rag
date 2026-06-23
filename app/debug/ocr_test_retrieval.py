from app.ingestion.retriever import retrieve

queries = [

    "According to the Legal Drafting and Writing notes, what are the two categories of legal drafting?",

    "According to the Legal Drafting and Writing notes, what is a lease agreement?",

    "According to the Legal Drafting and Writing notes, what is a charge sheet?"

]

for query in queries:

    print("\n" + "=" * 80)
    print("QUESTION:", query)

    results = retrieve(query, k=5)