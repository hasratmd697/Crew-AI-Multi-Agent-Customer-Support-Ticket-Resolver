import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env if present
load_dotenv()

# Project Paths
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
POLICIES_DIR = DATA_DIR / "policies"
VECTORSTORE_DIR = DATA_DIR / "vectorstore"
TEST_TICKETS_DIR = DATA_DIR / "test_tickets"

# Ensure directories exist
VECTORSTORE_DIR.mkdir(parents=True, exist_ok=True)
TEST_TICKETS_DIR.mkdir(parents=True, exist_ok=True)

# LLM Config
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL_NAME = os.getenv("OPENAI_MODEL_NAME", "gpt-4o-mini")
OPENAI_API_BASE = os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1")

# Embeddings Config
EMBEDDER_MODEL_NAME = "all-MiniLM-L6-v2"
CHROMA_COLLECTION_NAME = "ecommerce_policies"

# Retrieval Config
RETRIEVAL_TOP_K = 5
RETRIEVAL_SIMILARITY_THRESHOLD = 0.65

# Chunking Config
CHUNK_SIZE = 500
CHUNK_OVERLAP = 75
