from typing import List
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

def chunk_documents(documents: List[Document], chunk_size: int = 500, chunk_overlap: int = 75) -> List[Document]:
    """
    Splits documents into smaller chunks using RecursiveCharacterTextSplitter,
    which respects markdown headers and paragraphs.
    """
    # Use headers, paragraphs, and then words/characters to split
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n## ", "\n# ", "\n\n", "\n", " ", ""],
        add_start_index=True 
    )

    chunks = text_splitter.split_documents(documents)
    
    # Enhance the metadata of each chunk
    for i, chunk in enumerate(chunks):
        # We can extract the closest section header if we want, but simple approach is to search
        # the chunk text for "Section X.X" 
        section = "Unknown Section"
        for line in chunk.page_content.split('\n'):
            if "Section" in line and (line.startswith("## ") or line.startswith("# ")):
                section = line.strip("# ").strip()
                break
            elif "Section" in line.split(" - ")[0]:
                section = line.split(" - ")[0].strip()
                break
                
        chunk.metadata["chunk_id"] = f"{chunk.metadata['doc_id']}_chunk_{i}"
        
        # If the chunk doesn't explicitly contain the section header, that's okay, we do our best effort
        # A more advanced parser could track the active header during splitting.
        # But this is sufficient for our simple markdown format.
        if section != "Unknown Section":
            chunk.metadata["section"] = section
            
    return chunks

if __name__ == "__main__":
    import sys
    from pathlib import Path
    sys.path.append(str(Path(__file__).parent.parent.parent))
    
    from src.config import POLICIES_DIR, CHUNK_SIZE, CHUNK_OVERLAP
    from src.ingestion.loader import load_policy_documents
    
    docs = load_policy_documents(POLICIES_DIR)
    chunks = chunk_documents(docs, CHUNK_SIZE, CHUNK_OVERLAP)
    
    print(f"Split {len(docs)} documents into {len(chunks)} chunks.")
    print("Example chunk:")
    print(f"Content length: {len(chunks[0].page_content)}")
    print(f"Metadata: {chunks[0].metadata}")
