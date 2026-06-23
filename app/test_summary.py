import chromadb

from llm.summarizer import generate_summary


client = chromadb.PersistentClient(path="chroma_db")

collection = client.get_collection("legal_documents")


all_docs = collection.get(
    include=["metadatas"]
)

pdfs = sorted(
    {
        meta["pdf_name"]
        for meta in all_docs["metadatas"]
    }
)

print("\nAvailable PDFs:\n")

for pdf in pdfs:
    print(pdf)

pdf_name = input("\nEnter PDF name: ").strip()

results = collection.get(
    where={"pdf_name": pdf_name},
    include=["documents", "metadatas"]
)

if len(results["documents"]) == 0:
    print(f"\nNo chunks found for: {pdf_name}")
    exit()

chunks = []

for doc, metadata in zip(
    results["documents"],
    results["metadatas"]
):

    chunks.append(
        {
            "chunk_text": doc,
            "pdf_name": metadata["pdf_name"],
            "pdf_path": metadata["pdf_path"],
            "page_number": metadata["page_number"]
        }
    )

summary = generate_summary(
    chunks=chunks,
    pdf_name=chunks[0]["pdf_name"],
    pdf_path=chunks[0]["pdf_path"]
)

print("\n" + "=" * 60)
print("SUMMARY")
print("=" * 60)

print(summary)