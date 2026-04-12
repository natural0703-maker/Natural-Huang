from pathlib import Path

from src.docx_writer import build_output_docx_path
from tests.test_paths import make_test_dir


def test_output_naming_rule() -> None:
    tmp_path = make_test_dir("output_naming")
    input_path = tmp_path / "novel.docx"
    input_path.touch()

    first = build_output_docx_path(input_path, tmp_path)
    assert first.name == "novel_TW.docx"
    first.touch()

    second = build_output_docx_path(input_path, tmp_path)
    assert second.name == "novel_TW_001.docx"
    second.touch()

    third = build_output_docx_path(input_path, tmp_path)
    assert third.name == "novel_TW_002.docx"
