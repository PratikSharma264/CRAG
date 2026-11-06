"""The whole RAG flow for one chat question, as a stream of small events."""

from . import config, generation, retrieval


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
    """
    search_question = generation.condense_question(question, history or [])
    yield {"type": "query", "text": search_question}

    hits = retrieval.search(search_question, top_k=config.TOP_K)

    if not hits:
        yield {"type": "sources", "sources": [], "confidence": 0.0}
        yield {"type": "token", "text": config.NO_ANSWER}
        return

    yield {
        "type": "sources",
        "sources": build_sources(hits),
        "confidence": max(hit["similarity"] for hit in hits),
    }

    for text in generation.stream_answer(search_question, hits):
        yield {"type": "token", "text": text}
