"""
Input  : PaddleOCR-VL *_res.json files, nested per book under
         private/<book>/<extraction-batch>/raw/
Output : private/<book>/cleaned_data/filtered_blocks.json -> content blocks,
         in reading order

Text is NOT modified here, it:
  - keeps content blocks
  - drops noise blocks and empty blocks
  - extracts the printed page numbers
  - sorts everything in reading order

A book's filtered_blocks.json is regenerated from ALL of that book's raw
extraction batches on every run. Re-parsing already-OCR'd JSON is cheap, so
there's no incremental append/dedup logic to maintain as new chapters'
batches are added.
"""

import argparse
import json
import pathlib
from collections import Counter

from private_paths import book_cleaned_file, book_root, require_book_path

# Labels we keep. Everything else (image, footer, header, seal, ...) is dropped.
# "number" is dropped too, but we read the printed page number from it first.
KEEP_LABELS = {"text", "paragraph_title", "doc_title", "vision_footnote"}


def read_printed_page_number(page):
    """The 'number' block holds the page number printed in the book."""
    for block in page["parsing_res_list"]:
        if block["block_label"] == "number":
            value = block["block_content"].strip()
            if value.isdigit():
                return int(value)
    return None


def extract_content_blocks(page, printed_page):
    blocks = []
    for block in page["parsing_res_list"]:
        if block["block_label"] not in KEEP_LABELS:
            continue
        if not block["block_content"].strip():      # empty = layout false positive
            continue
        blocks.append({
            "page_index": page["page_index"],
            "printed_page": printed_page,
            "order": block["block_order"],
            "label": block["block_label"],
            "content": block["block_content"],
            "x": block["block_bbox"][0],
        })
    return blocks


def discover_raw_files(raw_root: pathlib.Path) -> list[pathlib.Path]:
    """All *_res.json files across every extraction batch under raw_root."""
    return sorted(
        raw_root.glob("*/raw/*_res.json"),
        key=lambda p: json.loads(p.read_text(encoding="utf-8"))["page_index"],
    )


def load_pages(raw_root: pathlib.Path):
    files = discover_raw_files(raw_root)
    if not files:
        raise SystemExit(f"no *_res.json files found under {raw_root}/*/raw/")
    return [json.loads(f.read_text(encoding="utf-8")) for f in files]


def regenerate_book(raw_root: pathlib.Path, output_file: pathlib.Path) -> list[dict]:
    """Parse every raw extraction batch under raw_root and write output_file.

    Always regenerates output_file from scratch: block extraction from
    already-OCR'd JSON is cheap, so there's no need to reconcile ordering
    or duplicates against a book's previously-cleaned batches.
    """
    blocks = []
    printed_pages = {}

    for page in load_pages(raw_root):
        printed_page = read_printed_page_number(page)
        printed_pages[page["page_index"]] = printed_page
        blocks.extend(extract_content_blocks(page, printed_page))

    # Reading order: page, then block_order.
    # block_order is None for captions, so we push them to the end of their page
    # instead of letting the sort crash on a None comparison.
    blocks.sort(key=lambda b: (b["page_index"],
                               b["order"] is None,
                               b["order"] or 0))

    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text(
        json.dumps(blocks, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    # --- report
    label_counts = Counter(b["label"] for b in blocks)
    print(f"{len(blocks)} blocks kept -> {output_file}")
    for label, count in label_counts.most_common():
        print(f"   {label:<16} {count}")
    print(f"printed pages: {[printed_pages[k] for k in sorted(printed_pages)]}")

    return blocks


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("book", help="book slug, e.g. 'hydratation'")
    args = parser.parse_args(argv)

    raw_root = book_root(args.book)
    require_book_path(raw_root, args.book)
    regenerate_book(raw_root, book_cleaned_file(args.book))


if __name__ == "__main__":
    main()
