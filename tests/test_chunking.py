import json

import chunking
from private_paths import book_cleaned_file


def make_block(label, content, page_index=0, order=1, printed_page=14, x=27):
    return {
        "page_index": page_index,
        "printed_page": printed_page,
        "order": order,
        "label": label,
        "content": content,
        "x": x,
    }


def test_title_followed_by_text_blocks_produces_one_chunk():
    blocks = [
        make_block("paragraph_title", "## TITLE", order=1),
        make_block("text", "first paragraph", order=2),
        make_block("text", "second paragraph", order=3),
    ]

    chunks, _ = chunking.chunk_blocks(blocks, book="hydratation")

    assert len(chunks) == 1
    assert chunks[0]["title"] == "## TITLE"
    assert "first paragraph" in chunks[0]["text"]
    assert "second paragraph" in chunks[0]["text"]


def test_doc_title_is_excluded_from_chunks_and_kept_as_book_metadata():
    blocks = [
        make_block("doc_title", "# BOOK TITLE", order=1),
        make_block("paragraph_title", "## TITLE", order=2),
        make_block("text", "some text", order=3),
    ]

    chunks, book_metadata = chunking.chunk_blocks(blocks, book="hydratation")

    assert all(c["title"] != "# BOOK TITLE" for c in chunks)
    assert all("BOOK TITLE" not in c["text"] for c in chunks)
    assert book_metadata["book"] == "hydratation"
    assert [dt["content"] for dt in book_metadata["doc_titles"]] == ["# BOOK TITLE"]


def test_oversized_section_is_split_on_paragraph_boundaries():
    blocks = [make_block("paragraph_title", "## TITLE", order=1)]
    for i in range(20):
        blocks.append(make_block("text", " ".join(["word"] * 20), order=i + 2))

    chunks, _ = chunking.chunk_blocks(blocks, book="hydratation", max_tokens=50)

    assert len(chunks) > 1
    assert all(c["title"] == "## TITLE" for c in chunks)


def test_chunk_includes_book_slug_and_underlying_block_metadata():
    blocks = [
        make_block("paragraph_title", "## TITLE", page_index=2, order=1),
        make_block("text", "body", page_index=2, order=2),
    ]

    chunks, _ = chunking.chunk_blocks(blocks, book="hydratation")

    assert chunks[0]["book"] == "hydratation"
    assert chunks[0]["blocks"][0]["page_index"] == 2
    assert chunks[0]["blocks"][0]["order"] == 1
    assert chunks[0]["blocks"][1]["order"] == 2


def test_leading_text_before_first_title_is_dropped_not_crashed_on():
    blocks = [
        make_block("text", "orphan preamble", order=1),
        make_block("paragraph_title", "## TITLE", order=2),
        make_block("text", "real content", order=3),
    ]

    chunks, _ = chunking.chunk_blocks(blocks, book="hydratation")

    assert len(chunks) == 1
    assert "orphan preamble" not in chunks[0]["text"]


def test_chunking_against_real_hydratation_filtered_blocks_json():
    blocks = json.loads(book_cleaned_file("hydratation").read_text(encoding="utf-8"))

    chunks, book_metadata = chunking.chunk_blocks(blocks, book="hydratation")

    assert len(chunks) > 0
    assert book_metadata["book"] == "hydratation"


def test_main_writes_chunks_and_book_metadata_to_the_book_chunks_file(tmp_path, monkeypatch):
    cleaned_file = tmp_path / "hydratation" / "cleaned_data" / "filtered_blocks.json"
    cleaned_file.parent.mkdir(parents=True)
    cleaned_file.write_text(json.dumps([
        make_block("paragraph_title", "## TITLE", order=1),
        make_block("text", "body", order=2),
    ]), encoding="utf-8")
    output_file = tmp_path / "hydratation" / "cleaned_data" / "chunks.json"

    monkeypatch.setattr(chunking, "book_cleaned_file", lambda book: cleaned_file)
    monkeypatch.setattr(chunking, "book_chunks_file", lambda book: output_file)

    chunking.main(["hydratation"])

    written = json.loads(output_file.read_text(encoding="utf-8"))
    assert written["book_metadata"]["book"] == "hydratation"
    assert len(written["chunks"]) == 1
    assert written["chunks"][0]["title"] == "## TITLE"
