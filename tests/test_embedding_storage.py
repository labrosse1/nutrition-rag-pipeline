import json

import pytest

import embedding_storage


def make_chunk(book="hydratation", title="## TITLE", text="body text", blocks=None):
    return {
        "book": book,
        "title": title,
        "text": text,
        "blocks": blocks or [
            {"page_index": 3, "printed_page": 17, "order": 1},
            {"page_index": 4, "printed_page": 18, "order": 1},
        ],
    }


def test_chunk_to_document_flattens_metadata_to_scalars():
    chunk = make_chunk()

    document = embedding_storage.chunk_to_document(chunk)

    assert document.text == "body text"
    assert document.metadata["book"] == "hydratation"
    assert document.metadata["title"] == "## TITLE"
    assert document.metadata["page_start"] == 3
    assert document.metadata["page_end"] == 4
    assert all(isinstance(v, (str, int, float, bool)) for v in document.metadata.values())


def test_chunk_to_document_preserves_full_block_metadata_as_json():
    chunk = make_chunk()

    document = embedding_storage.chunk_to_document(chunk)

    assert json.loads(document.metadata["blocks_json"]) == chunk["blocks"]


def test_chunk_to_document_handles_missing_title():
    chunk = make_chunk(title=None)

    document = embedding_storage.chunk_to_document(chunk)

    assert document.metadata["title"] == ""


def test_main_fails_fast_when_the_book_path_is_missing(tmp_path, monkeypatch):
    monkeypatch.setattr(
        embedding_storage, "book_chunks_file", lambda book: tmp_path / book / "chunks.json"
    )

    with pytest.raises(FileNotFoundError, match="missing-book"):
        embedding_storage.main(["missing-book"])
