import chromadb
from sentence_transformers import SentenceTransformer


client = chromadb.PersistentClient(path="./chroma_db")

try:
    client.delete_collection("legal_documents")
except:
    pass

collection = client.get_or_create_collection(
    name="legal_documents"
)

embedding_model = SentenceTransformer(
    "BAAI/bge-small-en-v1.5",
    trust_remote_code=True
)


def store_chunks(all_chunks):

    for i, chunk in enumerate(all_chunks):

        chunk_id = (
            f"{chunk['document_id']}_{chunk['chunk_id']}"
        )

        existing = collection.get(
            ids=[chunk_id]
        )
        
        if existing["ids"]:
            continue

        embedding = embedding_model.encode(
            chunk["chunk_text"],
            normalize_embeddings=True
        ).tolist()

        if i < 10:
            print(
                f"Stored -> "
                f"Doc: {chunk['document_id']} | "
                f"Chunk: {chunk['chunk_id']} | "
                f"Page: {chunk['page_number']}"
            )

        collection.add(
            ids=[chunk_id],
            documents=[chunk["chunk_text"]],
            embeddings=[embedding],
            metadatas=[
    {
        "pdf_name": chunk["pdf_name"],
        "source_document": chunk["pdf_name"],
        "pdf_path": chunk["pdf_path"],
        "page_number": chunk["page_number"],
        "document_id": chunk["document_id"],
        "chunk_id": chunk["chunk_id"],
        "heading": chunk["heading"],
    }
]
        )

    print(
        f"\nStored {len(all_chunks)} chunks."
    )

    print(
        "Collection count:",
        collection.count()
    )