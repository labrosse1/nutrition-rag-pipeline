import json

import pytest

import data_cleaning


def make_page(page_index, printed_page, blocks):
    """blocks: list of (label, content, order, x)."""
    parsing_res_list = []
    if printed_page is not None:
        parsing_res_list.append({
            "block_label": "number",
            "block_content": str(printed_page),
            "block_order": None,
            "block_bbox": [0, 0, 0, 0],
        })
    for label, content, order, x in blocks:
        parsing_res_list.append({
            "block_label": label,
            "block_content": content,
            "block_order": order,
            "block_bbox": [x, 0, 0, 0],
        })
    return {"page_index": page_index, "parsing_res_list": parsing_res_list}


def write_batch(raw_root, batch_name, pages):
    batch_dir = raw_root / batch_name / "raw"
    batch_dir.mkdir(parents=True)
    for page in pages:
        (batch_dir / f"hydratation_{page['page_index']}_res.json").write_text(
            json.dumps(page), encoding="utf-8"
        )


def test_read_printed_page_number_reads_the_number_block():
    page = make_page(0, 14, [])

    assert data_cleaning.read_printed_page_number(page) == 14


def test_read_printed_page_number_is_none_when_absent():
    page = {"page_index": 0, "parsing_res_list": []}

    assert data_cleaning.read_printed_page_number(page) is None


def test_extract_content_blocks_keeps_only_known_labels_and_drops_empty():
    page = make_page(0, 14, [
        ("paragraph_title", "## TITLE", 1, 27),
        ("text", "some body text", 2, 136),
        ("image", "irrelevant", 3, 10),
        ("text", "   ", 4, 50),
    ])

    blocks = data_cleaning.extract_content_blocks(page, printed_page=14)

    assert [b["label"] for b in blocks] == ["paragraph_title", "text"]
    assert [b["content"] for b in blocks] == ["## TITLE", "some body text"]
    assert all(b["printed_page"] == 14 for b in blocks)


def test_discover_raw_files_finds_files_across_multiple_batches_sorted_by_page(tmp_path):
    raw_root = tmp_path / "hydratation"
    write_batch(raw_root, "2026-08-31_vl16", [
        make_page(1, 15, [("text", "page two", 1, 10)]),
        make_page(0, 14, [("text", "page one", 1, 10)]),
    ])
    write_batch(raw_root, "2026-09-10_vl16", [
        make_page(2, 16, [("text", "page three", 1, 10)]),
    ])

    files = data_cleaning.discover_raw_files(raw_root)
    pages = [json.loads(f.read_text())["page_index"] for f in files]

    assert pages == [0, 1, 2]


def test_regenerate_book_writes_blocks_in_reading_order(tmp_path):
    raw_root = tmp_path / "hydratation"
    write_batch(raw_root, "2026-08-31_vl16", [
        make_page(0, 14, [
            ("text", "second block", 2, 136),
            ("paragraph_title", "## TITLE", 1, 27),
        ]),
    ])
    output_file = tmp_path / "hydratation" / "cleaned_data" / "filtered_blocks.json"

    blocks = data_cleaning.regenerate_book(raw_root, output_file)

    assert [b["label"] for b in blocks] == ["paragraph_title", "text"]
    assert output_file.exists()
    written = json.loads(output_file.read_text())
    assert written == blocks


def test_regenerate_book_regenerates_from_scratch_not_append(tmp_path):
    raw_root = tmp_path / "hydratation"
    output_file = raw_root / "cleaned_data" / "filtered_blocks.json"

    write_batch(raw_root, "2026-08-31_vl16", [
        make_page(0, 14, [("paragraph_title", "chapter one", 1, 27)]),
    ])
    first_run = data_cleaning.regenerate_book(raw_root, output_file)
    assert [b["content"] for b in first_run] == ["chapter one"]

    write_batch(raw_root, "2026-09-10_vl16", [
        make_page(1, 15, [("paragraph_title", "chapter two", 1, 27)]),
    ])
    second_run = data_cleaning.regenerate_book(raw_root, output_file)

    assert [b["content"] for b in second_run] == ["chapter one", "chapter two"]


def test_load_pages_raises_when_book_has_no_raw_batches(tmp_path):
    raw_root = tmp_path / "hydratation"
    raw_root.mkdir()

    with pytest.raises(SystemExit):
        data_cleaning.load_pages(raw_root)


def test_main_fails_fast_when_the_book_path_is_missing(tmp_path, monkeypatch):
    monkeypatch.setattr(data_cleaning, "book_root", lambda book: tmp_path / book)

    with pytest.raises(FileNotFoundError, match="missing-book"):
        data_cleaning.main(["missing-book"])
