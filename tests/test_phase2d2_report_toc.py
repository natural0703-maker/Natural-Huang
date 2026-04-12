import json
from pathlib import Path
from types import SimpleNamespace

from src.phase1_pipeline import Phase1StubResult
from src.phase1_reporter import build_phase1_report_payload, write_phase1_reports
from src.phase1_review_apply import ReviewApplyResult
from src.review_schema import ErrorRecord, ReviewSchema, TocState


def _result(
    operation: str,
    *,
    toc: TocState | None = None,
    errors: list[ErrorRecord] | None = None,
    output_path: Path | None = None,
    apply_result: ReviewApplyResult | None = None,
) -> Phase1StubResult:
    schema = ReviewSchema(toc=toc or TocState(), errors=errors or [])
    return Phase1StubResult(
        operation=operation,
        config_check=SimpleNamespace(warnings=()),
        schema=schema,
        message="",
        docx_processed=output_path is not None,
        output_path=output_path,
        apply_result=apply_result,
    )


def test_convert_report_includes_toc_status() -> None:
    payload = build_phase1_report_payload(
        _result(
            "convert",
            toc=TocState(requested=True, status="field_inserted", fallback_used=False, chapter_count=2),
            output_path=Path("converted.docx"),
        )
    )

    assert payload["toc"] == {
        "requested": True,
        "status": "field_inserted",
        "fallback_used": False,
        "chapter_count": 2,
    }
    assert "toc" not in payload["convert"]


def test_apply_review_report_includes_toc_status() -> None:
    apply_result = ReviewApplyResult(
        schema=ReviewSchema(),
        output_path=Path("reviewed.docx"),
        applied=False,
        candidate_results=[],
        applied_count=0,
        skipped_count=0,
        failed_count=0,
    )

    payload = build_phase1_report_payload(
        _result(
            "apply_review",
            toc=TocState(requested=True, status="field_inserted", fallback_used=False, chapter_count=1),
            output_path=Path("reviewed.docx"),
            apply_result=apply_result,
        )
    )

    assert payload["toc"]["status"] == "field_inserted"
    assert payload["toc"]["chapter_count"] == 1
    assert "toc" not in payload["apply_review"]


def test_fallback_chapter_list_keeps_success_true() -> None:
    payload = build_phase1_report_payload(
        _result(
            "convert",
            toc=TocState(requested=True, status="fallback_chapter_list", fallback_used=True, chapter_count=3),
        )
    )

    assert payload["toc"]["status"] == "fallback_chapter_list"
    assert payload["toc"]["fallback_used"] is True
    assert payload["success"] is True


def test_skipped_no_headings_keeps_success_true() -> None:
    payload = build_phase1_report_payload(
        _result("convert", toc=TocState(requested=True, status="skipped_no_headings", chapter_count=0))
    )

    assert payload["toc"]["status"] == "skipped_no_headings"
    assert payload["success"] is True


def test_not_requested_reports_default_toc_state() -> None:
    payload = build_phase1_report_payload(_result("analyze"))

    assert payload["toc"] == {
        "requested": False,
        "status": "not_requested",
        "fallback_used": False,
        "chapter_count": 0,
    }


def test_txt_report_includes_minimal_toc_summary(tmp_path) -> None:
    txt_path = tmp_path / "report.txt"
    result = _result(
        "convert",
        toc=TocState(requested=True, status="field_inserted", fallback_used=False, chapter_count=2),
    )

    write_phase1_reports(result, None, txt_path)

    text = txt_path.read_text(encoding="utf-8")
    assert "TOC 狀態：field_inserted" in text
    assert "TOC fallback：否" in text
    assert "TOC 章節數：2" in text


def test_json_report_writes_toc_payload(tmp_path) -> None:
    json_path = tmp_path / "report.json"
    result = _result(
        "convert",
        toc=TocState(requested=True, status="fallback_chapter_list", fallback_used=True, chapter_count=4),
    )

    write_phase1_reports(result, json_path, None)

    payload = json.loads(json_path.read_text(encoding="utf-8"))
    assert payload["toc"] == {
        "requested": True,
        "status": "fallback_chapter_list",
        "fallback_used": True,
        "chapter_count": 4,
    }


def test_success_depends_only_on_schema_errors_not_toc_status() -> None:
    success_payload = build_phase1_report_payload(
        _result("convert", toc=TocState(requested=True, status="failed", fallback_used=False, chapter_count=1))
    )
    error_payload = build_phase1_report_payload(
        _result(
            "convert",
            toc=TocState(requested=True, status="field_inserted", fallback_used=False, chapter_count=1),
            errors=[ErrorRecord(code="TOC_INSERT_FAILED", message="TOC 失敗")],
        )
    )

    assert success_payload["success"] is True
    assert error_payload["success"] is False
