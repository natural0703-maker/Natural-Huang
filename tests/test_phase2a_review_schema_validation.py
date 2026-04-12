import json
from pathlib import Path

from docx import Document

from src.phase1_pipeline import Phase1Options, apply_review
from tests.test_paths import make_test_dir


def _make_docx(path: Path, paragraphs: list[str] | None = None) -> None:
    document = Document()
    for text in paragraphs or ["資訊"]:
        document.add_paragraph(text)
    document.save(path)


def _write_payload(path: Path, payload) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")


def _candidate(**overrides):
    data = {
        "candidate_id": "risk:one",
        "type": "high_risk_term",
        "status": "accepted",
        "source_text": "資訊",
        "resolved_text": "訊息",
        "paragraph_index": 0,
        "char_start": 0,
        "char_end": 2,
        "context_before": "",
        "context_after": "",
    }
    data.update(overrides)
    return data


def _apply_payload(payload):
    tmp = make_test_dir("phase2a_review_schema_validation")
    input_path = tmp / "source.docx"
    review_path = tmp / "review.json"
    output_dir = tmp / "out"
    _make_docx(input_path)
    _write_payload(review_path, payload)
    return apply_review(Phase1Options(input_path=input_path, output_dir=output_dir, apply_review_path=review_path))


def _assert_flow_error(payload, code: str):
    result = _apply_payload(payload)

    assert result.docx_processed is False
    assert result.output_path is None
    assert result.schema.errors
    assert result.schema.errors[0].code == code
    assert result.apply_result is not None
    assert result.apply_result.candidate_results == []
    return result


def test_reviewed_json_root_must_be_object() -> None:
    _assert_flow_error([], "REVIEW_JSON_ROOT_INVALID")


def test_review_candidates_must_be_list_when_present() -> None:
    _assert_flow_error({"review_candidates": {}}, "REVIEW_CANDIDATES_INVALID")


def test_review_candidates_can_be_missing() -> None:
    result = _apply_payload({})

    assert result.schema.errors == []
    assert result.apply_result is not None
    assert result.apply_result.candidate_results == []
    assert result.output_path is not None
    assert result.output_path.exists()


def test_review_candidate_must_be_object() -> None:
    _assert_flow_error({"review_candidates": ["bad"]}, "REVIEW_CANDIDATE_INVALID")


def test_review_candidate_id_is_required() -> None:
    _assert_flow_error({"review_candidates": [_candidate(candidate_id="")]}, "REVIEW_CANDIDATE_ID_INVALID")
    _assert_flow_error(
        {"review_candidates": [{key: value for key, value in _candidate().items() if key != "candidate_id"}]},
        "REVIEW_CANDIDATE_ID_INVALID",
    )


def test_review_candidate_status_must_be_supported() -> None:
    _assert_flow_error({"review_candidates": [_candidate(status="done")]}, "REVIEW_CANDIDATE_STATUS_INVALID")


def test_review_candidate_status_auto_accepted_is_not_allowed() -> None:
    result = _assert_flow_error(
        {"review_candidates": [_candidate(status="auto_accepted")]},
        "REVIEW_CANDIDATE_STATUS_INVALID",
    )

    assert "auto_accepted" in result.schema.errors[0].message


def test_review_candidate_source_text_is_required() -> None:
    _assert_flow_error({"review_candidates": [_candidate(source_text="")]}, "REVIEW_CANDIDATE_SOURCE_TEXT_INVALID")
    _assert_flow_error(
        {"review_candidates": [{key: value for key, value in _candidate().items() if key != "source_text"}]},
        "REVIEW_CANDIDATE_SOURCE_TEXT_INVALID",
    )


def test_review_candidate_paragraph_index_must_be_non_negative_integer() -> None:
    _assert_flow_error(
        {"review_candidates": [_candidate(paragraph_index="0")]},
        "REVIEW_CANDIDATE_PARAGRAPH_INDEX_INVALID",
    )
    _assert_flow_error(
        {"review_candidates": [_candidate(paragraph_index=-1)]},
        "REVIEW_CANDIDATE_PARAGRAPH_INDEX_INVALID",
    )


def test_review_candidate_span_must_be_valid_integer_range() -> None:
    _assert_flow_error({"review_candidates": [_candidate(char_start="0")]}, "REVIEW_CANDIDATE_SPAN_INVALID")
    _assert_flow_error({"review_candidates": [_candidate(char_end="2")]}, "REVIEW_CANDIDATE_SPAN_INVALID")
    _assert_flow_error({"review_candidates": [_candidate(char_start=-1)]}, "REVIEW_CANDIDATE_SPAN_INVALID")
    _assert_flow_error({"review_candidates": [_candidate(char_start=2, char_end=2)]}, "REVIEW_CANDIDATE_SPAN_INVALID")


def test_review_candidate_context_must_be_string_when_present() -> None:
    _assert_flow_error(
        {"review_candidates": [_candidate(context_before=[])]},
        "REVIEW_CANDIDATE_CONTEXT_INVALID",
    )
    _assert_flow_error(
        {"review_candidates": [_candidate(context_after={})]},
        "REVIEW_CANDIDATE_CONTEXT_INVALID",
    )


def test_review_candidate_type_must_be_string() -> None:
    _assert_flow_error({"review_candidates": [_candidate(type=123)]}, "REVIEW_CANDIDATE_TYPE_INVALID")


def test_unsupported_string_type_is_candidate_level_skipped() -> None:
    result = _apply_payload({"review_candidates": [_candidate(type="chapter")]})

    assert result.schema.errors == []
    assert result.apply_result is not None
    assert result.apply_result.candidate_results[0].result_code == "SKIPPED_UNSUPPORTED_TYPE"
    assert result.apply_result.skipped_count == 1
