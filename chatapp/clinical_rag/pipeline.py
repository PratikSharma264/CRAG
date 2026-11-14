"""The whole RAG flow for one chat question, as a stream of small events."""

from . import config, generation, retrieval
from .sufficiency import engine, SufficiencyError


def build_sources(hits):
    """What the chat shows under an answer: which abstract and chunk each passage came from."""
    sources = []
    for hit in hits:
        meta = hit["metadata"]
        filename = meta.get("source", "Unknown")
        stem = filename[:-4] if filename.lower().endswith(".txt") else filename
        chunk = meta.get("chunk_index")

        parts = []
        if isinstance(chunk, int):
            parts.append(f"Chunk {chunk + 1}")
        parts.append(f"similarity {hit['similarity']:.2f}")

        sources.append({
            "source": filename,
            "title": stem,
            "chunk": chunk,
            "meta": " \u00b7 ".join(parts),
            "score": round(hit["similarity"], 3),
        })
    return sources


def stream_rag_answer(question, history=None):
    """
    Generator of events:
      {"type": "query", "text": "..."}                         the question that was searched
      {"type": "sources", "sources": [...], "confidence": f}   the retrieved abstracts
      {"type": "token", "text": "..."}                         (many) the answer
      {"type": "abstain", "reason": "...", "details": {...}}   evidence insufficient
      {"type": "error", "message": "..."}                      operational error
    """
    search_question = generation.condense_question(question, history or [])
    yield {"type": "query", "text": search_question}

    hits = retrieval.search(search_question, top_k=config.TOP_K)

    if not hits:
        yield {"type": "sources", "sources": [], "confidence": 0.0}
        # No passages retrieved: abstain with explanation
        yield {
            "type": "abstain",
            "reason": "No relevant passages found in the knowledge base.",
            "details": {
                "combined_score": 0.0,
                "threshold": config.COMBINED_THRESHOLD,
                "model_c_probability": 0.0,
                "cosine_similarity": 0.0,
                "check_details": {"empty_retrieval": True},
            },
        }
        return

    # Evaluate sufficiency before generation (fail-closed)
    try:
        sufficiency = engine.evaluate(search_question, hits)
    except SufficiencyError as e:
        # Operational error (Model C missing, inference failure, etc.) - fail closed
        yield {
            "type": "error",
            "message": f"Sufficiency evaluation failed: {e}",
        }
        return

    yield {
        "type": "sources",
        "sources": build_sources(hits),
        "confidence": max(hit["similarity"] for hit in hits),
    }

    if not sufficiency.sufficient:
        # Evidence insufficient: yield abstain event and stop
        yield {
            "type": "abstain",
            "reason": (
                "The retrieved passages were not considered sufficient to answer the question. "
                "The combined sufficiency score is below the required threshold."
            ),
            "details": {
                "combined_score": sufficiency.combined_score,
                "threshold": sufficiency.threshold,
                "model_c_probability": sufficiency.model_c_probability,
                "cosine_similarity": sufficiency.cosine_similarity,
                "check_details": sufficiency.check_details,
            },
        }
        return

    # Evidence sufficient: proceed with generation
    for text in generation.stream_answer(search_question, hits):
        yield {"type": "token", "text": text}
