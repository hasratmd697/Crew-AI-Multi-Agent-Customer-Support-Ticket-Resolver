import os
from pathlib import Path
from typing import List, Dict, Any
from langchain_core.documents import Document

def load_policy_documents(policies_dir: str | Path) -> List[Document]:
    """
    Loads all markdown files from the policies directory.
    Returns a list of LangChain Document objects.
    """
    policies_path = Path(policies_dir)
    documents = []
    
    if not policies_path.exists():
        raise FileNotFoundError(f"Policies directory not found: {policies_path}")

    # Process all markdown files
    for md_file in policies_path.glob("*.md"):
        with open(md_file, "r", encoding="utf-8") as f:
            content = f.read()
            
            # Simple metadata extraction based on the synthetic policy structure
            filename = md_file.name
            
            # Assume first line is the Title: `# Title`
            lines = content.split('\n')
            title = filename
            for line in lines:
                if line.startswith('# '):
                    title = line.replace('# ', '').strip()
                    break
                    
            doc = Document(
                page_content=content,
                metadata={
                    "doc_id": filename,
                    "doc_title": title,
                    "source": str(md_file)
                }
            )
            documents.append(doc)
            
    return documents

if __name__ == "__main__":
    import sys
    sys.path.append(str(Path(__file__).parent.parent.parent))
    from src.config import POLICIES_DIR
    
    docs = load_policy_documents(POLICIES_DIR)
    print(f"Loaded {len(docs)} documents.")
    for d in docs[:2]:
        print(f" - {d.metadata['doc_title']}")
