"""Access to the ChromaDB collection that ingest.py builds."""

from functools import lru_cache

from . import config


class KnowledgeBaseNotReady(RuntimeError):
    """The vector database is missing or empty. The message is safe to show to users."""


@lru_cache(maxsize=2)
def _client(path):
    import chromadb

    return chromadb.PersistentClient(path=path)


def get_collection():
    try:
        collection = _client(str(config.VECTOR_DB_PATH)).get_collection(name=config.COLLECTION_NAME)
    except Exception as exc:
        raise KnowledgeBaseNotReady(
            "The knowledge base has not been indexed yet. "
            "Run `python ingest.py`, then restart the server."
        ) from exc

    if collection.count() == 0:
        raise KnowledgeBaseNotReady(
            "The knowledge base is empty. Add .txt files to the knowledge_base folder, "
            "run `python ingest.py`, then restart the server."
        )
    return collection
