import json
from pathlib import Path
from types import SimpleNamespace

from src.phase1_pipeline import Phase1StubResult
from src.phase1_reporter import build_phase1_report_payload, write_phase1_reports
from src.phase1_review_apply import ReviewApplyCandidateResult, ReviewApplyResult
from src.review_schema import ErrorRecord, ReviewCandidate, ReviewSchema


def _result(
    operation: str,
    *,
    schema: ReviewSchema | None = None,
    output_path: Path | None = None,
    config_warnings: tuple[str, ...] = (),
    apply_result: ReviewApplyResult | None = None,
) -> Phase1StubResult:
    return Phase1StubResult(
        operation=operation,
        config_check=SimpleNamespace(warnings=config_warnings),
        schema=schema or ReviewSchema(),
        message="",
        docx_processed=output_path is not None,
        output_path=output_path,
        apply_result=apply_result,
    )


def test_json_payload_key_order_and_null_output_path() -> None:
    payload = build_phase1_report_payload(_result("analyze"))

    assert list(payload.keys()) == [
        "schema_version",
        "operation",
        "success",
        "output_path",
        "counts",
        "toc",
        "paragraph_merge",
        "paragraph_merge_diagnostics",
        "config_warnings",
        "errors",
        "analyze",
    ]
    assert payload["output_path"] is None


def test_success_depends_only_on_schema_errors() -> None:
    apply_result = ReviewApplyResult(
        schema=ReviewSchema(),
        output_path=Path("reviewed.docx"),
        applied=False,
        candidate_results=[
            ReviewApplyCandidateResult(
                candidate_id="risk:1",
                status="accepted",
                result_code="APPLY_TARGET_NOT_FOUND",
                paragraph_index=0,
                applied=False,
                message="failed",
            )
        ],
        applied_count=0,
        skipped_count=0,
        failed_count=1,
    )

    payload = build_phase1_report_payload(
        _result("apply_review", output_path=Path("reviewed.docx"), apply_result=apply_result)
    )

    assert payload["success"] is True
    assert payload["counts"]["failed"] == 1


def test_config_warnings_are_written_to_json_and_txt(tmp_path) -> None:
    result = _result("analyze", config_warnings=("設定警告",))
    json_path = tmp_path / "report.json"
    txt_path = tmp_path / "report.txt"

    write_result = write_phase1_reports(result, json_path, txt_path)

    assert write_result.errors == []
    payload = json.loads(json_path.read_text(encoding="utf-8"))
    assert payload["config_warnings"] == ["設定警告"]
    assert "設定警告數：1" in txt_path.read_text(encoding="utf-8")


def test_txt_report_includes_first_schema_error(tmp_path) -> None:
    schema = ReviewSchema(errors=[ErrorRecord(code="INPUT_NOT_FOUND", message="找不到檔案")])
    txt_path = tmp_path / "report.txt"

    write_phase1_reports(_result("analyze", schema=schema), None, txt_path)

    text = txt_path.read_text(encoding="utf-8")
    assert "錯誤數：1" in text
    assert "第一個錯誤：INPUT_NOT_FOUND 找不到檔案" in text


def test_json_write_failure_does_not_block_txt(monkeypatch, tmp_path) -> None:
    original_write_text = Path.write_text

    def fake_write_text(self, *args, **kwargs):
        if self.suffix == ".json":
            raise OSError("json failed")
        return original_write_text(self, *args, **kwargs)

    monkeypatch.setattr(Path, "write_text", fake_write_text)
    json_path = tmp_path / "report.json"
    txt_path = tmp_path / "report.txt"

    result = write_phase1_reports(_result("analyze"), json_path, txt_path)

    assert [error.code for error in result.errors] == ["REPORT_JSON_WRITE_FAILED"]
    assert result.json_report_path is None
    assert result.txt_report_path == txt_path
    assert txt_path.exists()


def test_txt_write_failure_does_not_block_json(monkeypatch, tmp_path) -> None:
    original_write_text = Path.write_text

    def fake_write_text(self, *args, **kwargs):
        if self.suffix == ".txt":
            raise OSError("txt failed")
        return original_write_text(self, *args, **kwargs)

    monkeypatch.setattr(Path, "write_text", fake_write_text)
    json_path = tmp_path / "report.json"
    txt_path = tmp_path / "report.txt"

    result = write_phase1_reports(_result("analyze"), json_path, txt_path)

    assert [error.code for error in result.errors] == ["REPORT_TXT_WRITE_FAILED"]
    assert result.json_report_path == json_path
    assert result.txt_report_path is None
    assert json.loads(json_path.read_text(encoding="utf-8"))["success"] is True


def test_none_paths_do_not_write_or_fail() -> None:
    result = write_phase1_reports(_result("analyze"), None, None)

    assert result.json_report_path is None
    assert result.txt_report_path is None
    assert result.errors == []


def test_counts_include_review_candidates() -> None:
    schema = ReviewSchema(review_candidates=[ReviewCandidate(candidate_id="risk:1")])

    payload = build_phase1_report_payload(_result("convert", schema=schema, output_path=Path("out.docx")))

    assert payload["counts"]["review_candidates"] == 1
    assert payload["convert"]["output_path"] == "out.docx"
