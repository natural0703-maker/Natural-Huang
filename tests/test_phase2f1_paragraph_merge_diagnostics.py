import json
from pathlib import Path
from types import SimpleNamespace

from docx import Document

from src.phase1_pipeline import Phase1StubResult
from src.phase1_reporter import build_phase1_report_payload, write_phase1_reports
from src.phase1_review_apply import (
    ParagraphMergeDiagnostics,
    ParagraphMergeSummary,
    ReviewApplyCandidateResult,
    ReviewApplyResult,
    apply_review_docx,
    build_paragraph_merge_diagnostics,
)
from src.review_schema import ErrorRecord, ReviewSchema, TocState


def _write_docx(path: Path, paragraphs: list[str]) -> None:
    document = Document()
    for paragraph in paragraphs:
        document.add_paragraph(paragraph)
    document.save(path)


def _write_review_json(path: Path, paragraph_merge_candidates: list[dict]) -> None:
    path.write_text(
        json.dumps({"paragraph_merge_candidates": paragraph_merge_candidates}, ensure_ascii=False),
        encoding="utf-8",
    )


def _merge_candidate(
    candidate_id: str,
    *,
    source_text: str,
    next_source_text: str,
) -> dict:
    return {
        "candidate_id": candidate_id,
        "type": "paragraph_merge",
        "status": "accepted",
        "paragraph_index": 0,
        "next_paragraph_index": 1,
        "source_text": source_text,
        "next_source_text": next_source_text,
    }


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


def _apply_result_with_diagnostics(diagnostics: ParagraphMergeDiagnostics) -> ReviewApplyResult:
    return ReviewApplyResult(
        schema=ReviewSchema(toc=TocState(requested=True, status="field_inserted", chapter_count=1)),
        output_path=Path("reviewed.docx"),
        applied=False,
        candidate_results=[],
        applied_count=0,
        skipped_count=0,
        failed_count=1,
        paragraph_merge_summary=ParagraphMergeSummary(
            failed_count=1,
            codes={"PARAGRAPH_MERGE_SOURCE_MISMATCH": 1},
        ),
        paragraph_merge_diagnostics=diagnostics,
    )


def test_source_and_next_source_mismatch_are_counted(tmp_path) -> None:
    input_path = tmp_path / "input.docx"
    review_path = tmp_path / "review.json"
    output_dir = tmp_path / "out"
    _write_docx(input_path, ["前段目前文字", "後段目前文字"])
    _write_review_json(
        review_path,
        [
            _merge_candidate("merge:source", source_text="前段舊文字", next_source_text="後段目前文字"),
            _merge_candidate("merge:next", source_text="前段目前文字", next_source_text="後段舊文字"),
        ],
    )

    result = apply_review_docx(input_path, review_path, output_dir, create_toc=False)

    assert result.paragraph_merge_diagnostics.source_mismatch_count == 1
    assert result.paragraph_merge_diagnostics.next_source_mismatch_count == 1
    assert result.paragraph_merge_diagnostics.total_mismatch_count == 2
    assert result.paragraph_merge_diagnostics.sample_candidate_ids == ["merge:source", "merge:next"]
    assert [item.result_code for item in result.candidate_results] == [
        "PARAGRAPH_MERGE_SOURCE_MISMATCH",
        "PARAGRAPH_MERGE_SOURCE_MISMATCH",
    ]


def test_sample_candidate_ids_keep_first_three_in_encounter_order() -> None:
    diagnostics = build_paragraph_merge_diagnostics(
        [
            ReviewApplyCandidateResult(f"merge:{index}", "accepted", "PARAGRAPH_MERGE_SOURCE_MISMATCH", 0, False, "", "SOURCE_TEXT_MISMATCH")
            for index in range(5)
        ]
    )

    assert diagnostics.source_mismatch_count == 5
    assert diagnostics.next_source_mismatch_count == 0
    assert diagnostics.total_mismatch_count == 5
    assert diagnostics.sample_candidate_ids == ["merge:0", "merge:1", "merge:2"]


def test_json_report_contains_top_level_paragraph_merge_diagnostics() -> None:
    diagnostics = ParagraphMergeDiagnostics(
        source_mismatch_count=2,
        next_source_mismatch_count=1,
        total_mismatch_count=3,
        sample_candidate_ids=["merge:a", "merge:b"],
    )

    payload = build_phase1_report_payload(
        _phase1_result(
            "apply_review",
            output_path=Path("reviewed.docx"),
            apply_result=_apply_result_with_diagnostics(diagnostics),
        )
    )

    assert payload["paragraph_merge_diagnostics"] == {
        "total_mismatch_count": 3,
        "source_mismatch_count": 2,
        "next_source_mismatch_count": 1,
        "sample_candidate_ids": ["merge:a", "merge:b"],
    }
    assert "paragraph_merge_diagnostics" not in payload["paragraph_merge"]


def test_analyze_and_convert_reports_keep_default_empty_diagnostics() -> None:
    expected = {
        "total_mismatch_count": 0,
        "source_mismatch_count": 0,
        "next_source_mismatch_count": 0,
        "sample_candidate_ids": [],
    }

    analyze_payload = build_phase1_report_payload(_phase1_result("analyze"))
    convert_payload = build_phase1_report_payload(_phase1_result("convert", output_path=Path("converted.docx")))

    assert analyze_payload["paragraph_merge_diagnostics"] == expected
    assert convert_payload["paragraph_merge_diagnostics"] == expected


def test_txt_report_contains_minimal_diagnostics_summary(tmp_path) -> None:
    txt_path = tmp_path / "report.txt"
    diagnostics = ParagraphMergeDiagnostics(
        source_mismatch_count=1,
        next_source_mismatch_count=1,
        total_mismatch_count=2,
        sample_candidate_ids=["merge:a", "merge:b"],
    )

    write_phase1_reports(
        _phase1_result(
            "apply_review",
            output_path=Path("reviewed.docx"),
            apply_result=_apply_result_with_diagnostics(diagnostics),
        ),
        None,
        txt_path,
    )

    text = txt_path.read_text(encoding="utf-8")
    assert "段落合併 mismatch 總數：2" in text
    assert "段落合併前段 mismatch：1" in text
    assert "段落合併後段 mismatch：1" in text
    assert "段落合併 mismatch 範例候選：merge:a, merge:b" in text


def test_txt_report_uses_none_for_empty_diagnostics_samples(tmp_path) -> None:
    txt_path = tmp_path / "report.txt"

    write_phase1_reports(_phase1_result("analyze"), None, txt_path)

    text = txt_path.read_text(encoding="utf-8")
    assert "段落合併 mismatch 範例候選：無" in text


def test_success_depends_only_on_schema_errors_not_diagnostics() -> None:
    diagnostics = ParagraphMergeDiagnostics(
        source_mismatch_count=1,
        total_mismatch_count=1,
        sample_candidate_ids=["merge:1"],
    )

    success_payload = build_phase1_report_payload(
        _phase1_result("apply_review", apply_result=_apply_result_with_diagnostics(diagnostics))
    )
    error_payload = build_phase1_report_payload(
        _phase1_result(
            "apply_review",
            schema=ReviewSchema(errors=[ErrorRecord(code="INPUT_NOT_FOUND", message="missing")]),
            apply_result=_apply_result_with_diagnostics(ParagraphMergeDiagnostics()),
        )
    )

    assert success_payload["success"] is True
    assert error_payload["success"] is False


def test_diagnostics_do_not_change_paragraph_merge_summary_or_toc_payload() -> None:
    diagnostics = ParagraphMergeDiagnostics(
        source_mismatch_count=1,
        total_mismatch_count=1,
        sample_candidate_ids=["merge:1"],
    )

    payload = build_phase1_report_payload(
        _phase1_result(
            "apply_review",
            schema=ReviewSchema(toc=TocState(requested=True, status="field_inserted", chapter_count=3)),
            apply_result=_apply_result_with_diagnostics(diagnostics),
        )
    )

    assert payload["paragraph_merge"] == {
        "applied_count": 0,
        "skipped_count": 0,
        "failed_count": 1,
        "codes": {"PARAGRAPH_MERGE_SOURCE_MISMATCH": 1},
    }
    assert payload["toc"] == {
        "requested": True,
        "status": "field_inserted",
        "fallback_used": False,
        "chapter_count": 3,
    }
