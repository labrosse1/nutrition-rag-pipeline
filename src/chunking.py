"""
Input  : private/<book>/cleaned_data/filtered_blocks.json -> content blocks,
         in reading order (the shape produced by data_cleaning.py)
Output : private/<book>/cleaned_data/chunks.json -> retrieval-ready chunks
         and book-level metadata

Pure logic lives in chunk_blocks (no file I/O, no network calls): a
paragraph_title block starts a chunk, absorbing the blocks that follow it
until the next paragraph_title/doc_title or the end of input. doc_title
blocks are never part of a chunk; they're collected as book-level metadata.
A chunk whose merged text exceeds a max-token cap is split further on
paragraph (block) boundaries, all pieces still tagged with the same title.

Token counts are approximated by whitespace-split word count, which is
close enough for a cap meant to keep chunks embedding-model-sized -- no
tokenizer dependency needed for that.
"""

import argparse
import json

from private_paths import book_chunks_file, book_cleaned_file, require_book_path

DEFAULT_MAX_TOKENS = 300


def _approx_tokens(text: str) -> int:
    return len(text.split())


def _merged_text(blocks: list[dict]) -> str:
    return "\n\n".join(b["content"] for b in blocks)


def _block_metadata(block: dict) -> dict:
    return {
        "page_index": block["page_index"],
        "printed_page": block["printed_page"],
        "order": block["order"],
    }


def _build_chunk(book: str, title: str | None, blocks: list[dict]) -> dict:
    return {
        "book": book,
        "title": title,
        "text": _merged_text(blocks),
        "blocks": [_block_metadata(b) for b in blocks],
    }


def _split_on_token_cap(
    book: str, title: str | None, blocks: list[dict], max_tokens: int
) -> list[dict]:
    """Split blocks into chunks whose merged text stays near max_tokens,
    splitting only on block (paragraph) boundaries."""
    chunks = []
    current = []
    current_tokens = 0

    for block in blocks:
        block_tokens = _approx_tokens(block["content"])
        if current and current_tokens + block_tokens > max_tokens:
            chunks.append(_build_chunk(book, title, current))
            current = []
            current_tokens = 0
        current.append(block)
        current_tokens += block_tokens

    if current:
        chunks.append(_build_chunk(book, title, current))

    return chunks


def chunk_blocks(
    blocks: list[dict], book: str, max_tokens: int = DEFAULT_MAX_TOKENS
) -> tuple[list[dict], dict]:
    """Group blocks into title-anchored chunks plus book-level metadata.

    Returns (chunks, book_metadata).
    """
    chunks = []
    doc_titles = []
    title = None
    pending_blocks = []

    def flush():
        if not pending_blocks:
            return
        if _approx_tokens(_merged_text(pending_blocks)) > max_tokens:
            chunks.extend(_split_on_token_cap(book, title, pending_blocks, max_tokens))
        else:
            chunks.append(_build_chunk(book, title, pending_blocks))

    for block in blocks:
        if block["label"] == "doc_title":
            flush()
            pending_blocks = []
            title = None
            doc_titles.append(_block_metadata(block) | {"content": block["content"]})
        elif block["label"] == "paragraph_title":
            flush()
            title = block["content"]
            pending_blocks = [block]
        else:
            if title is None:
                # No title has been seen yet: nothing to anchor these blocks to.
                continue
            pending_blocks.append(block)

    flush()

    book_metadata = {"book": book, "doc_titles": doc_titles}
    return chunks, book_metadata


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("book", help="book slug, e.g. 'hydratation'")
    args = parser.parse_args(argv)

    cleaned_file = book_cleaned_file(args.book)
    require_book_path(cleaned_file, args.book)
    blocks = json.loads(cleaned_file.read_text(encoding="utf-8"))

    chunks, book_metadata = chunk_blocks(blocks, args.book)

    output_file = book_chunks_file(args.book)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text(
        json.dumps({"book_metadata": book_metadata, "chunks": chunks},
                   ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(f"{len(chunks)} chunks -> {output_file}")


if __name__ == "__main__":
    main()
