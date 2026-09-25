from pathlib import Path

import chromadb
from sentence_transformers import SentenceTransformer


# --------------------------------------------------
# Configuration
# --------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent
DOCS_DIR = BASE_DIR / "docs"
CHROMA_DIR = BASE_DIR / "chroma_db"

COLLECTION_NAME = "zepto_policies"
EMBEDDING_MODEL = "all-MiniLM-L6-v2"


# --------------------------------------------------
# Load policy documents
# --------------------------------------------------

def load_documents():
    documents = []

    for file_path in sorted(DOCS_DIR.glob("*.txt")):
        text = file_path.read_text(encoding="utf-8").strip()

        if not text:
            print(f"WARNING: Empty document: {file_path.name}")
            continue

        documents.append(
            {
                "filename": file_path.name,
                "text": text,
            }
        )

    return documents


# --------------------------------------------------
# Simple document chunking
# --------------------------------------------------

def create_chunks(documents):
    chunks = []

    for document in documents:
        chunks.append(
            {
                "id": document["filename"].replace(".txt", ""),
                "text": document["text"],
                "source": document["filename"],
            }
        )

    return chunks


# --------------------------------------------------
# Store embeddings in ChromaDB
# --------------------------------------------------

def build_vector_store(chunks):
    print(f"Loading embedding model: {EMBEDDING_MODEL}")

    model = SentenceTransformer(EMBEDDING_MODEL)

    texts = [chunk["text"] for chunk in chunks]

    embeddings = model.encode(
        texts,
        convert_to_numpy=True,
        show_progress_bar=True,
    ).tolist()

    print(f"Creating ChromaDB database: {CHROMA_DIR}")

    client = chromadb.PersistentClient(
        path=str(CHROMA_DIR)
    )

    # Recreate the collection to guarantee cosine similarity retrieval.
    try:
        client.delete_collection(name=COLLECTION_NAME)
    except Exception:
        pass

    collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={
            "description": "Zepto customer support policies",
            "hnsw:space": "cosine",
        },
    )

    collection.upsert(
        ids=[chunk["id"] for chunk in chunks],
        documents=texts,
        embeddings=embeddings,
        metadatas=[
            {
                "source": chunk["source"]
            }
            for chunk in chunks
        ],
    )

    return collection


# --------------------------------------------------
# Main
# --------------------------------------------------

def main():
    print("=" * 60)
    print("Zepto Support Assistant - Document Ingestion")
    print("=" * 60)

    documents = load_documents()

    print(f"\nDocuments found: {len(documents)}")

    for document in documents:
        print(f"  - {document['filename']}")

    if len(documents) != 8:
        raise RuntimeError(
            f"Expected 8 policy documents, but found {len(documents)}."
        )

    chunks = create_chunks(documents)

    print(f"\nChunks created: {len(chunks)}")

    collection = build_vector_store(chunks)

    print("\n" + "=" * 60)
    print("Ingestion completed successfully")
    print("=" * 60)
    print(f"Collection: {COLLECTION_NAME}")
    print(f"Documents stored: {collection.count()}")
    print(f"Database location: {CHROMA_DIR}")


if __name__ == "__main__":
    main()