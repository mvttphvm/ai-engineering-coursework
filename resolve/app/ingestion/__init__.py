"""Layer 1a — ingestion: load documents, clean them, chunk them."""
from app.ingestion.chunking import Chunk, chunk_text
from app.ingestion.loaders import LoadedDocument, load_directory, load_file
from app.ingestion.pipeline import ingest_directory, ingest_texts

__all__ = [
    "Chunk",
    "chunk_text",
    "LoadedDocument",
    "load_directory",
    "load_file",
    "ingest_directory",
    "ingest_texts",
]
