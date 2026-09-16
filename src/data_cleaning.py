
"""
Input  : PaddleOCR-VL *_res.json files
Output : filtered_blocks.json -> content blocks, in reading order

Text is NOT modified here, it:
  - keeps content blocks
  - drops noise blocks and empty blocks
  - extracts the printed page numbers
  - sorts everything in reading order
"""

import json
import pathlib
from collections import Counter

# Anchored on this file, not on the current working directory, so the script
# can be run from anywhere.
ROOT = pathlib.Path(__file__).resolve().parent.parent
RAW_DIR = ROOT / "private" / "2026-08-31_vl16" / "raw"
OUTPUT_FILE = ROOT / "private" / "cleaned_data" / "filtered_blocks.json"

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


def load_pages():
    files = sorted(
        RAW_DIR.glob("*_res.json"),
        key=lambda p: json.loads(p.read_text(encoding="utf-8"))["page_index"],
    )
    if not files:
        raise SystemExit(f"no *_res.json files found in {RAW_DIR}")
    return [json.loads(f.read_text(encoding="utf-8")) for f in files]


def main():
    blocks = []
    printed_pages = {}

    for page in load_pages():
        printed_page = read_printed_page_number(page)
        printed_pages[page["page_index"]] = printed_page
        blocks.extend(extract_content_blocks(page, printed_page))

    # Reading order: page, then block_order.
    # block_order is None for captions, so we push them to the end of their page
    # instead of letting the sort crash on a None comparison.
    blocks.sort(key=lambda b: (b["page_index"],
                               b["order"] is None,
                               b["order"] or 0))

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_FILE.write_text(
        json.dumps(blocks, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    # --- report
    label_counts = Counter(b["label"] for b in blocks)
    print(f"{len(blocks)} blocks kept -> {OUTPUT_FILE}")
    for label, count in label_counts.most_common():
        print(f"   {label:<16} {count}")
    print(f"printed pages: {[printed_pages[k] for k in sorted(printed_pages)]}")


if __name__ == "__main__":
    main()