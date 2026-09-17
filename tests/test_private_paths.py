import pytest

import private_paths


def test_book_root_is_nested_under_private_root(tmp_path, monkeypatch):
    monkeypatch.setattr(private_paths, "PRIVATE_ROOT", tmp_path)

    assert private_paths.book_root("hydratation") == tmp_path / "hydratation"


def test_book_cleaned_file_is_nested_under_the_book(tmp_path, monkeypatch):
    monkeypatch.setattr(private_paths, "PRIVATE_ROOT", tmp_path)

    assert private_paths.book_cleaned_file("hydratation") == (
        tmp_path / "hydratation" / "cleaned_data" / "filtered_blocks.json"
    )


def test_require_book_path_raises_with_missing_path_named(tmp_path):
    missing = tmp_path / "hydratation"

    with pytest.raises(FileNotFoundError) as excinfo:
        private_paths.require_book_path(missing, "hydratation")

    message = str(excinfo.value)
    assert str(missing) in message
    assert "hydratation" in message


def test_require_book_path_passes_silently_when_path_exists(tmp_path):
    existing = tmp_path / "hydratation"
    existing.mkdir()

    private_paths.require_book_path(existing, "hydratation")
