"""
Shared paths and guard for the private submodule.

Copyrighted extraction artifacts (raw OCR output, cleaned blocks, and
eventually the vector store) live only under `private/`, nested per book.
Any pipeline entry point that reads from `private/` should call
`require_book_path` before touching the filesystem, so a missing or
un-initialized submodule fails fast with a clear message instead of a
confusing downstream stack trace.
"""

import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
PRIVATE_ROOT = ROOT / "private"


def book_root(book: str) -> pathlib.Path:
    """The book's folder: `<date>_vl16/raw/` batches live directly under it,
    alongside its `cleaned_data/`."""
    return PRIVATE_ROOT / book


def book_cleaned_file(book: str) -> pathlib.Path:
    return book_root(book) / "cleaned_data" / "filtered_blocks.json"


def require_book_path(path: pathlib.Path, book: str) -> None:
    if not path.exists():
        raise FileNotFoundError(
            f"expected private data for book '{book}' at {path}, but it's "
            "missing. Did you run `git submodule update --init` for the "
            "`private` submodule?"
        )
