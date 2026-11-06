"""Search the knowledge base (same query logic as query.py)."""

from . import config, encoders
from .store import get_collection


def search(question, top_k=None):
    """
    Return the chunks most similar to the question, best first.

    Each hit is a dict: id, content, metadata, distance, similarity (1 - cosine distance), rank.
    """
    top_k = top_k or config.TOP_K

    collection = get_collection()
    query_embedding = encoders.encode_query(question)

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=min(top_k, collection.count()),
    )

    hits = []
    for rank, (doc_id, doc, meta, dist) in enumerate(
        zip(
            results["ids"][0],
            results["documents"][0],
            results["metadatas"][0],
            results["distances"][0],
        ),
        start=1,
    ):
        hits.append({
            "id": doc_id,
            "content": doc,
            "metadata": meta or {},
            "distance": dist,
            "similarity": 1 - dist,   # cosine distance: lower is more similar
            "rank": rank,
        })
    return hits
