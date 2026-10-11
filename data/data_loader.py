from pathlib import Path

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

def load_documents(file_path):
    """Load nutrition data from a text file."""

    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(
            f"File not found: {path.resolve()}"
        )

    text = path.read_text(encoding="utf-8")

    if not text.strip():
        raise ValueError("The nutrition data file is empty.")

    return [
        Document(
            page_content=text,
            metadata={"source": str(path)}
        )
    ]

def split_documents(documents):
    """Split the loaded text into smaller chunks."""

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200
    )

    return splitter.split_documents(documents)

if __name__ == "__main__":
    documents = load_documents("data/NFCMS_DATA.txt")
    chunks = split_documents(documents)

    print(f"Documents loaded: {len(documents)}")
    print(f"Chunks created: {len(chunks)}")

    if chunks:
        print("\nFirst chunk:")
    print(chunks[0].page_content[:500])







    
