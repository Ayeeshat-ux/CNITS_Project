# src/vector_store.py

from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings

from src.data_loader import load_documents, split_documents


def create_vector_store():
    documents = load_documents("data/NFCMS_DATA.txt")
    chunks = split_documents(documents)

    if not chunks:
        raise ValueError("No text chunks were created.")

    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )
    vector_store = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory="chroma_db",
        collection_name="nutrition_data",
    )

    print(f"Documents loaded: {len(documents)}")
    print(f"Chunks stored: {len(chunks)}")
    print("ChromaDB vector store created successfully.")

    return vector_store


if __name__ == "__main__":
    create_vector_store()