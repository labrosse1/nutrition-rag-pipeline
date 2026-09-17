"""
Input  : private/<book>/cleaned_data/chunks.json -> chunks produced by
         chunking.py
Output : private/<book>/vector_store/ -> a Chroma persistent collection
         holding each chunk's OpenAI text-embedding-3-small embedding, plus
         enough metadata for retrieval. Never written outside private/.

Wired through llama-index so the embedding step shares its orchestration
(config, retries) with the existing Gemini generation setup
(llama-index-llms-google-genai).
"""

import argparse
import json
import pathlib

import chromadb
from llama_index.core import Document, StorageContext, VectorStoreIndex
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.vector_stores.chroma import ChromaVectorStore

from private_paths import book_chunks_file, book_vector_store_dir, require_book_path

EMBED_MODEL = "text-embedding-3-small"
COLLECTION_NAME = "chunks"


def chunk_to_document(chunk: dict) -> Document:
    """Chroma metadata values must be scalars, so a chunk's block list is
    flattened to its page range, plus a JSON string for full fidelity."""
    pages = [b["page_index"] for b in chunk["blocks"]]
    return Document(
        text=chunk["text"],
        metadata={
            "book": chunk["book"],
            "title": chunk["title"] or "",
            "page_start": min(pages),
            "page_end": max(pages),
            "blocks_json": json.dumps(chunk["blocks"]),
        },
    )


def embed_and_store(
    chunks: list[dict], book: str, persist_dir: pathlib.Path | None = None
) -> VectorStoreIndex:
    """Embed each chunk with OpenAI text-embedding-3-small and persist the
    vectors, plus retrieval metadata, into a Chroma store at persist_dir
    (defaults to that book's vector_store folder inside the private
    submodule)."""
    persist_dir = persist_dir or book_vector_store_dir(book)
    persist_dir.mkdir(parents=True, exist_ok=True)

    client = chromadb.PersistentClient(path=str(persist_dir))
    collection = client.get_or_create_collection(COLLECTION_NAME)
    vector_store = ChromaVectorStore(chroma_collection=collection)
    storage_context = StorageContext.from_defaults(vector_store=vector_store)

    documents = [chunk_to_document(chunk) for chunk in chunks]
    return VectorStoreIndex.from_documents(
        documents,
        storage_context=storage_context,
        embed_model=OpenAIEmbedding(model=EMBED_MODEL),
    )


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("book", help="book slug, e.g. 'hydratation'")
    args = parser.parse_args(argv)

    chunks_file = book_chunks_file(args.book)
    require_book_path(chunks_file, args.book)
    chunks = json.loads(chunks_file.read_text(encoding="utf-8"))["chunks"]

    persist_dir = book_vector_store_dir(args.book)
    embed_and_store(chunks, args.book, persist_dir)
    print(f"{len(chunks)} chunks embedded -> {persist_dir}")


if __name__ == "__main__":
    main()
