"""Read-only listing of the papers in the knowledge_base folder."""

from django.utils.text import slugify

from . import config


def list_documents():
    """Return the .txt files in knowledge_base/ (the same files ingest.py reads), sorted by name."""
    folder = config.KNOWLEDGE_BASE_PATH
    if not folder.is_dir():
        return []

    files = sorted(
        (path for path in folder.glob("*.txt") if path.is_file()),
        key=lambda path: path.name.casefold(),
    )
    return [{"stem": path.stem, "filename": path.name, "slug": slugify(path.stem)} for path in files]
