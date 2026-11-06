"""
Settings for the Clinical RAG pipeline.

These values mirror the standalone scripts (ingest.py and query.py) and must stay in sync
with them: the same encoders, the same ChromaDB collection and the same Groq model.
"""

from pathlib import Path

# <project root>/chatapp/clinical_rag/config.py  ->  parents[2] is the folder with manage.py
PROJECT_ROOT = Path(__file__).resolve().parents[2]

KNOWLEDGE_BASE_PATH = PROJECT_ROOT / "knowledge_base"
VECTOR_DB_PATH = PROJECT_ROOT / "vector_db"

# ChromaDB
COLLECTION_NAME = "research_abstracts"

# MedCPT (asymmetric: articles use the Article Encoder in ingest.py, queries use the Query Encoder)
ARTICLE_MODEL_NAME = "ncbi/MedCPT-Article-Encoder"
QUERY_MODEL_NAME = "ncbi/MedCPT-Query-Encoder"
MAX_TOKENS = 512
TOP_K = 3

# Groq
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
# GROQ_MODEL = "openai/gpt-oss-20b"
GROQ_MODEL = "openai/gpt-oss-120b"
TEMPERATURE = 0.2

SYSTEM_PROMPT = (
    "You are a helpful medical assistant specializing in diabetes for children and adolescents. "
    "Use ONLY the provided context to answer the user's question. "
    "If the answer cannot be found in the context, say 'I cannot find the answer in the provided documents.'"
)
NO_ANSWER = "I cannot find the answer in the provided documents."

# Chat feature (not part of query.py): when a conversation already has messages, a follow-up such as
# "what about adolescents?" is first rewritten into a standalone question using the same Groq model.
# Set to False to search with exactly what the user typed.
CONDENSE_FOLLOW_UPS = True
