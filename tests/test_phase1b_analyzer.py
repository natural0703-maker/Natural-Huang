from pathlib import Path

from docx import Document

from src.phase1_analyzer import CONTEXT_WINDOW
from src.phase1_pipeline import Phase1Options, analyze, apply_review, convert
from tests.test_paths import make_test_dir


def _make_docx(path: Path, paragraphs: list[str]) -> None:
    document = Document()
    for text in paragraphs:
        document.add_paragraph(text)
    document.save(path)


def test_analyze_reads_docx_without_modifying_input() -> None:
    tmp = make_test_dir("phase1b_analyze")
    input_path = tmp / "novel.docx"
    _make_docx(input_path, ["\u7b2c\u5341\u7ae0 \u591c\u96e8", "\u8cc7\u8a0a\u8cc7\u8a0a"])
    before_size = input_path.stat().st_size
    before_mtime = input_path.stat().st_mtime_ns

    result = analyze(Phase1Options(input_path=input_path))

    assert result.operation == "analyze"
    assert result.docx_processed is False
    assert result.schema.errors == []
    assert input_path.stat().st_size == before_size
    assert input_path.stat().st_mtime_ns == before_mtime
    assert len(result.schema.chapter_candidates) == 1
    chapter = result.schema.chapter_candidates[0]
    assert chapter.status == "pending"
    assert chapter.auto_accept is False
    assert chapter.source_text == "\u7b2c\u5341\u7ae0 \u591c\u96e8"
    assert len(result.schema.review_candidates) >= 2
    assert result.schema.paragraph_merge_candidates == []
    for candidate in result.schema.review_candidates:
        assert candidate.status == "pending"
        assert candidate.resolved_text == ""


def test_analyze_keeps_repeated_high_risk_hits() -> None:
    tmp = make_test_dir("phase1b_repeated_risk")
    input_path = tmp / "risk.docx"
    _make_docx(input_path, ["\u8cc7\u8a0a\u8cc7\u8a0a"])

    result = analyze(Phase1Options(input_path=input_path))

    matches = [
        candidate
        for candidate in result.schema.review_candidates
        if candidate.source_text == "\u8cc7\u8a0a"
    ]
    assert len(matches) == 2
    assert [item.char_start for item in matches] == [0, 2]
    assert len({item.rule_id for item in matches}) == 1


def test_high_risk_context_window_is_limited() -> None:
    tmp = make_test_dir("phase1b_context_window")
    input_path = tmp / "context.docx"
    _make_docx(input_path, ["\u524d" * 20 + "\u8cc7\u8a0a" + "\u5f8c" * 20])

    result = analyze(Phase1Options(input_path=input_path))

    matches = [
        candidate
        for candidate in result.schema.review_candidates
        if candidate.source_text == "\u8cc7\u8a0a"
    ]
    assert matches
    for match in matches:
        assert len(match.context_before) <= CONTEXT_WINDOW
        assert len(match.context_after) <= CONTEXT_WINDOW


def test_analyze_detects_paragraph_merge_candidate() -> None:
    tmp = make_test_dir("phase1b_merge_candidate")
    input_path = tmp / "merge.docx"
    _make_docx(input_path, ["他停下腳步，回頭看向", "遠方燈火慢慢亮起。"])

    result = analyze(Phase1Options(input_path=input_path))

    assert len(result.schema.paragraph_merge_candidates) == 1
    candidate = result.schema.paragraph_merge_candidates[0]
    assert candidate.status == "pending"
    assert candidate.auto_apply is False
    assert candidate.paragraph_index == 0
    assert candidate.next_paragraph_index == 1
    assert candidate.reason


def test_analyze_does_not_detect_merge_when_previous_has_sentence_end() -> None:
    tmp = make_test_dir("phase1b_merge_sentence_end")
    input_path = tmp / "sentence_end.docx"
    _make_docx(input_path, ["他停下腳步。", "遠方逐漸亮起的燈火。"])

    result = analyze(Phase1Options(input_path=input_path))

    assert result.schema.paragraph_merge_candidates == []


def test_analyze_does_not_detect_merge_for_dialogue() -> None:
    tmp = make_test_dir("phase1b_merge_dialogue")
    input_path = tmp / "dialogue.docx"
    _make_docx(input_path, ["「他停下腳步，回頭看向", "遠方逐漸亮起的燈火。"])

    result = analyze(Phase1Options(input_path=input_path))

    assert result.schema.paragraph_merge_candidates == []


def test_analyze_does_not_detect_merge_near_chapter_title() -> None:
    tmp = make_test_dir("phase1b_merge_chapter")
    input_path = tmp / "chapter.docx"
    _make_docx(input_path, ["第十章 夜雨", "遠方逐漸亮起的燈火。"])

    result = analyze(Phase1Options(input_path=input_path))

    assert result.schema.paragraph_merge_candidates == []


def test_analyze_does_not_detect_merge_for_high_risk_paragraph() -> None:
    tmp = make_test_dir("phase1b_merge_high_risk")
    input_path = tmp / "high_risk.docx"
    _make_docx(input_path, ["他停下腳步，資訊看向", "遠方逐漸亮起的燈火。"])

    result = analyze(Phase1Options(input_path=input_path))

    assert result.schema.review_candidates
    assert result.schema.paragraph_merge_candidates == []


def test_analyze_does_not_detect_merge_when_next_is_too_short() -> None:
    tmp = make_test_dir("phase1b_merge_short_next")
    input_path = tmp / "short_next.docx"
    _make_docx(input_path, ["他停下腳步，回頭看向", "燈。"])

    result = analyze(Phase1Options(input_path=input_path))

    assert result.schema.paragraph_merge_candidates == []


def test_analyze_does_not_detect_merge_for_plain_symbols_or_digits() -> None:
    tmp = make_test_dir("phase1b_merge_symbols_digits")
    input_path = tmp / "symbols_digits.docx"
    _make_docx(input_path, ["12345678", "遠方逐漸亮起的燈火。", "他停下腳步，回頭看向", "----"])

    result = analyze(Phase1Options(input_path=input_path))

    assert result.schema.paragraph_merge_candidates == []


def test_analyze_without_input_returns_empty_schema() -> None:
    result = analyze(Phase1Options())

    assert result.operation == "analyze"
    assert result.docx_processed is False
    assert result.schema.chapter_candidates == []
    assert result.schema.review_candidates == []
    assert result.schema.paragraph_merge_candidates == []
    assert result.schema.errors == []


def test_analyze_missing_file_returns_schema_error() -> None:
    result = analyze(Phase1Options(input_path=Path("missing.docx")))

    assert result.operation == "analyze"
    assert result.docx_processed is False
    assert result.schema.errors
    assert result.schema.errors[0].code == "INPUT_NOT_FOUND"
    assert result.schema.chapter_candidates == []
    assert result.schema.review_candidates == []
    assert result.schema.paragraph_merge_candidates == []


def test_analyze_non_docx_returns_schema_error() -> None:
    tmp = make_test_dir("phase1b_non_docx")
    input_path = tmp / "not_docx.txt"
    input_path.write_text("\u7b2c\u5341\u7ae0", encoding="utf-8")

    result = analyze(Phase1Options(input_path=input_path))

    assert result.operation == "analyze"
    assert result.docx_processed is False
    assert result.schema.errors
    assert result.schema.errors[0].code == "INPUT_NOT_DOCX"
    assert result.schema.chapter_candidates == []
    assert result.schema.review_candidates == []
    assert result.schema.paragraph_merge_candidates == []


def test_convert_without_input_returns_schema_error() -> None:
    result = convert(Phase1Options())

    assert result.operation == "convert"
    assert result.docx_processed is False
    assert result.schema.chapter_candidates == []
    assert result.schema.review_candidates == []
    assert result.schema.paragraph_merge_candidates == []
    assert result.schema.errors
    assert result.schema.errors[0].code == "INPUT_NOT_FOUND"


def test_apply_review_without_input_returns_schema_error() -> None:
    result = apply_review(Phase1Options())

    assert result.operation == "apply_review"
    assert result.docx_processed is False
    assert result.schema.errors
    assert result.schema.errors[0].code == "INPUT_NOT_FOUND"
