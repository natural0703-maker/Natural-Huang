import json
from pathlib import Path
from types import SimpleNamespace

from src.phase1_pipeline import Phase1StubResult
from src.phase1_reporter import build_phase1_report_payload, write_phase1_reports
from src.phase1_review_apply import (
    ParagraphMergeSummary,
    ReviewApplyCandidateResult,
    ReviewApplyResult,
    build_paragraph_merge_summary,
)
from src.review_schema import ErrorRecord, ReviewSchema, TocState


def _candidate_result(code: str, *, applied: bool = False) -> ReviewApplyCandidateResult:
    return ReviewApplyCandidateResult(
        candidate_id=f"candidate:{code}",
        status="accepted",
        result_code=code,
        paragraph_index=0,
        applied=applied,
        message="",
    )


def _phase1_result(
    operation: str,
    *,
    schema: ReviewSchema | None = None,
    output_path: Path | None = None,
    apply_result: ReviewApplyResult | None = None,
) -> Phase1StubResult:
    return Phase1StubResult(
        operation=operation,
        config_check=SimpleNamespace(warnings=()),
        schema=schema or ReviewSchema(),
        message="",
        docx_processed=output_path is not None,
        output_path=output_path,
        apply_result=apply_result,
    )


def _apply_result_with_summary(summary: ParagraphMergeSummary) -> ReviewApplyResult:
    return ReviewApplyResult(
        schema=ReviewSchema(toc=TocState(requested=True, status="field_inserted", chapter_count=1)),
        output_path=Path("reviewed.docx"),
        applied=True,
        candidate_results=[],
        applied_count=0,
        skipped_count=0,
        failed_count=0,
        paragraph_merge_summary=summary,
    )


def test_paragraph_merge_summary_counts_applied_skipped_failed_and_codes() -> None:
    summary = build_paragraph_merge_summary(
        [
            _candidate_result("APPLIED_PARAGRAPH_MERGE", applied=True),
            _candidate_result("SKIPPED_PARAGRAPH_MERGE_STATUS"),
            _candidate_result("PARAGRAPH_MERGE_CONFLICT"),
            _candidate_result("PARAGRAPH_MERGE_SOURCE_MISMATCH"),
            _candidate_result("PARAGRAPH_MERGE_APPLY_FAILED"),
            _candidate_result("APPLIED_CHAPTER_HEADING", applied=True),
            _candidate_result("APPLIED"),
        ]
    )

    assert summary.applied_count == 1
    assert summary.skipped_count == 2
    assert summary.failed_count == 2
    assert summary.codes == {
        "APPLIED_PARAGRAPH_MERGE": 1,
        "PARAGRAPH_MERGE_APPLY_FAILED": 1,
        "PARAGRAPH_MERGE_CONFLICT": 1,
        "PARAGRAPH_MERGE_SOURCE_MISMATCH": 1,
        "SKIPPED_PARAGRAPH_MERGE_STATUS": 1,
    }


def test_json_report_contains_top_level_paragraph_merge_summary() -> None:
    apply_result = _apply_result_with_summary(
        ParagraphMergeSummary(
            applied_count=2,
            skipped_count=1,
            failed_count=1,
            codes={"APPLIED_PARAGRAPH_MERGE": 2, "PARAGRAPH_MERGE_SOURCE_MISMATCH": 1},
        )
    )

    payload = build_phase1_report_payload(
        _phase1_result("apply_review", output_path=Path("reviewed.docx"), apply_result=apply_result)
    )

    assert payload["paragraph_merge"] == {
        "applied_count": 2,
        "skipped_count": 1,
        "failed_count": 1,
        "codes": {"APPLIED_PARAGRAPH_MERGE": 2, "PARAGRAPH_MERGE_SOURCE_MISMATCH": 1},
    }
    assert "paragraph_merge" not in payload["apply_review"]


def test_analyze_and_convert_reports_keep_default_empty_paragraph_merge_summary() -> None:
    analyze_payload = build_phase1_report_payload(_phase1_result("analyze"))
    convert_payload = build_phase1_report_payload(_phase1_result("convert", output_path=Path("converted.docx")))

    expected = {
        "applied_count": 0,
        "skipped_count": 0,
        "failed_count": 0,
        "codes": {},
    }
    assert analyze_payload["paragraph_merge"] == expected
    assert convert_payload["paragraph_merge"] == expected


def test_txt_report_contains_minimal_paragraph_merge_summary(tmp_path) -> None:
    txt_path = tmp_path / "report.txt"
    apply_result = _apply_result_with_summary(
        ParagraphMergeSummary(
            applied_count=1,
            skipped_count=1,
            failed_count=1,
            codes={"APPLIED_PARAGRAPH_MERGE": 1, "PARAGRAPH_MERGE_SOURCE_MISMATCH": 1},
        )
    )

    write_phase1_reports(
        _phase1_result("apply_review", output_path=Path("reviewed.docx"), apply_result=apply_result),
        None,
        txt_path,
    )

    text = txt_path.read_text(encoding="utf-8")
    assert "段落合併套用數：1" in text
    assert "段落合併略過數：1" in text
    assert "段落合併失敗數：1" in text
    assert "段落合併結果碼摘要：" in text
    assert "APPLIED_PARAGRAPH_MERGE=1" in text
    assert "PARAGRAPH_MERGE_SOURCE_MISMATCH=1" in text


def test_txt_report_uses_none_for_empty_paragraph_merge_codes(tmp_path) -> None:
    txt_path = tmp_path / "report.txt"

    write_phase1_reports(_phase1_result("analyze"), None, txt_path)

    assert "段落合併結果碼摘要：無" in txt_path.read_text(encoding="utf-8")


def test_success_still_depends_only_on_schema_errors_not_merge_summary() -> None:
    failed_merge = ParagraphMergeSummary(
        applied_count=0,
        skipped_count=0,
        failed_count=1,
        codes={"PARAGRAPH_MERGE_SOURCE_MISMATCH": 1},
    )
    success_payload = build_phase1_report_payload(
        _phase1_result("apply_review", apply_result=_apply_result_with_summary(failed_merge))
    )
    error_payload = build_phase1_report_payload(
        _phase1_result(
            "apply_review",
            schema=ReviewSchema(errors=[ErrorRecord(code="INPUT_NOT_FOUND", message="missing")]),
            apply_result=_apply_result_with_summary(ParagraphMergeSummary()),
        )
    )

    assert success_payload["success"] is True
    assert error_payload["success"] is False


def test_paragraph_merge_summary_does_not_change_toc_payload() -> None:
    apply_result = _apply_result_with_summary(
        ParagraphMergeSummary(applied_count=1, codes={"APPLIED_PARAGRAPH_MERGE": 1})
    )

    payload = build_phase1_report_payload(
        _phase1_result(
            "apply_review",
            schema=ReviewSchema(toc=TocState(requested=True, status="field_inserted", chapter_count=3)),
            apply_result=apply_result,
        )
    )

    assert payload["toc"] == {
        "requested": True,
        "status": "field_inserted",
        "fallback_used": False,
        "chapter_count": 3,
    }


def test_json_report_writes_paragraph_merge_summary(tmp_path) -> None:
    json_path = tmp_path / "report.json"
    apply_result = _apply_result_with_summary(
        ParagraphMergeSummary(applied_count=1, codes={"APPLIED_PARAGRAPH_MERGE": 1})
    )

    write_phase1_reports(
        _phase1_result("apply_review", output_path=Path("reviewed.docx"), apply_result=apply_result),
        json_path,
        None,
    )

    payload = json.loads(json_path.read_text(encoding="utf-8"))
    assert payload["paragraph_merge"]["applied_count"] == 1
    assert payload["paragraph_merge"]["codes"] == {"APPLIED_PARAGRAPH_MERGE": 1}
