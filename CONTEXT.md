# Nutrition RAG Pipeline

A retrieval-augmented generation pipeline built on a single copyrighted source book (currently `hydratation.pdf`). Extraction output is copyrighted and lives in a private submodule, kept separate from the public pipeline code.

## Language

**Extraction**:
The PaddleOCR-VL run over the source PDF, producing one raw `*_res.json` file per page in `private/<date>_vl16/raw/`. This is the single canonical extraction method for the pipeline.
_Avoid_: OCR run (ambiguous with the one-off GPT-5.6 cost estimate in `pricing_gpt.py`, which is not part of the pipeline).

**Block**:
The atomic unit produced from an extraction's raw page JSON: one `paragraph_title`, `text`, `doc_title`, or `vision_footnote` element, carrying its page index, printed page number, and reading order. Blocks are the output of `data_cleaning.py` / `filtered_blocks.json`.
_Avoid_: fragment, segment.

**Chunk**:
The retrieval unit fed to the embedding model: a `paragraph_title` block merged with the `text` blocks that follow it, up to the next title (split further on a max-token cap if oversized). One chunk = one titled section of one book. `doc_title` blocks are not chunked; they're kept as book-level metadata.
_Avoid_: block (a chunk is built from blocks, one step downstream), passage.

**Book**:
One source PDF (e.g. `hydratation.pdf`) and everything derived from it: its extraction batches, cleaned blocks, and chunks. The corpus is multi-book: more nutrition books will be extracted over time, and a book's own chapters may be extracted incrementally across several extraction batches before the book is complete.
_Avoid_: document, source (too generic — "book" is the unit the whole pipeline is namespaced by).
