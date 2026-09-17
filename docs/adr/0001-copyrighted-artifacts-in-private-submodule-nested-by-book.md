# Copyrighted artifacts live in the private submodule, nested by book

All artifacts derived from copyrighted source material — raw extraction JSON, cleaned blocks, and the eventual embedding/vector store — live in the `private` git submodule (`labrosse1/RAG-PIPELINE-COPYRIGHTED-DOCS`), never in the public repo. This keeps the public repo's pipeline code fully shareable regardless of what source books it's been pointed at.

Within `private/`, artifacts are nested per book (`private/<book>/<extraction-date>_vl16/raw/`, `private/<book>/cleaned_data/filtered_blocks.json`, ...), even though only one book (`hydratation`) exists today. The corpus is expected to grow to multiple books, and a single book's chapters may be extracted incrementally across several dated extraction batches before the book is complete. Nesting by book from the start avoids a migration once a second book or a second extraction batch shows up.

`data_cleaning.py` regenerates a book's entire `filtered_blocks.json` from all of that book's raw folders on every run, rather than appending new chapters incrementally — block extraction from already-OCR'd JSON is cheap, so always-regenerate avoids ordering/dedup reconciliation logic for negligible cost.

Public pipeline code that expects the submodule must fail fast with a clear error if the expected private path is missing, rather than crashing deep in the pipeline.
