import os
import shutil
from pathlib import Path
from langchain_chroma import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings

from ..config import (
    VECTORSTORE_DIR, 
    CHROMA_COLLECTION_NAME, 
    EMBEDDER_MODEL_NAME, 
    POLICIES_DIR,
    CHUNK_SIZE,
    CHUNK_OVERLAP
)
from .loader import load_policy_documents
from .chunker import chunk_documents

def get_embeddings_model():
    """Initialize the HuggingFace embeddings model."""
    return HuggingFaceEmbeddings(model_name=EMBEDDER_MODEL_NAME)

def build_vectorstore(force_rebuild: bool = True):
    """
    Loads documents, chunks them, and builds a new Chroma vectorstore.
    """
    print("Initializing embedding model...")
    embeddings = get_embeddings_model()
    
    if force_rebuild and VECTORSTORE_DIR.exists():
        print(f"Clearing existing vectorstore at {VECTORSTORE_DIR}...")
        shutil.rmtree(VECTORSTORE_DIR)
        VECTORSTORE_DIR.mkdir(parents=True)
        
    print(f"Loading policies from {POLICIES_DIR}...")
    docs = load_policy_documents(POLICIES_DIR)
    
    print(f"Chunking {len(docs)} documents...")
    chunks = chunk_documents(docs, CHUNK_SIZE, CHUNK_OVERLAP)
    
    print(f"Embedding {len(chunks)} chunks into ChromaDB at {VECTORSTORE_DIR}...")
    vectorstore = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        collection_name=CHROMA_COLLECTION_NAME,
        persist_directory=str(VECTORSTORE_DIR)
    )
    
    print("Vectorstore built and persisted successfully.")
    return vectorstore

def get_retriever():
    """
    Returns a retriever configured for the policy vectorstore.
    """
    embeddings = get_embeddings_model()
    vectorstore = Chroma(
        collection_name=CHROMA_COLLECTION_NAME,
        embedding_function=embeddings,
        persist_directory=str(VECTORSTORE_DIR)
    )
    # Configure retriever with similarity threshold and top_k
    return vectorstore.as_retriever(
        search_type="similarity",
        search_kwargs={"k": 5}
    )

if __name__ == "__main__":
    import sys
    sys.path.append(str(Path(__file__).parent.parent.parent))
    build_vectorstore()
