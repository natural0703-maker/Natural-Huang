from pathlib import Path
from types import SimpleNamespace

import pytest

import src.phase1_cli as phase1_cli
from src.phase1_reporter import ReportWriteResult
from src.phase1_pipeline import Phase1StubResult
from src.review_schema import ErrorRecord, ReviewSchema


def _result(operation: str, *, errors: list[ErrorRecord] | None = None, output_path: Path | None = None):
    return Phase1StubResult(
        operation=operation,
        config_check=None,
        schema=ReviewSchema(errors=errors or []),
        message="",
        docx_processed=output_path is not None,
        output_path=output_path,
    )


def test_cli_dispatches_apply_review_only_with_apply_review(monkeypatch) -> None:
    calls: list[str] = []

    def fake_apply_review(options):
        calls.append("apply_review")
        return _result("apply_review", output_path=Path("out.docx"))

    monkeypatch.setattr(phase1_cli, "apply_review", fake_apply_review)

    assert phase1_cli.main(["--apply-review", "review.json"]) == 0
    assert calls == ["apply_review"]


def test_cli_reviewed_output_alone_dispatches_analyze(monkeypatch) -> None:
    calls: list[str] = []

    def fake_analyze(options):
        calls.append("analyze")
        return _result("analyze")

    monkeypatch.setattr(phase1_cli, "analyze", fake_analyze)

    assert phase1_cli.main(["--reviewed-output", "reviewed.docx"]) == 0
    assert calls == ["analyze"]


def test_cli_reviewed_output_with_output_dir_dispatches_convert(monkeypatch) -> None:
    calls: list[str] = []

    def fake_convert(options):
        calls.append("convert")
        return _result("convert", output_path=Path("converted.docx"))

    monkeypatch.setattr(phase1_cli, "convert", fake_convert)

    assert phase1_cli.main(["--reviewed-output", "reviewed.docx", "--output-dir", "out"]) == 0
    assert calls == ["convert"]


def test_cli_apply_review_receives_reviewed_output_path(monkeypatch) -> None:
    received: list[Path | None] = []

    def fake_apply_review(options):
        received.append(options.reviewed_output_path)
        return _result("apply_review", output_path=Path("reviewed.docx"))

    monkeypatch.setattr(phase1_cli, "apply_review", fake_apply_review)

    assert phase1_cli.main(["--apply-review", "review.json", "--reviewed-output", "exact.docx"]) == 0
    assert received == [Path("exact.docx")]


def test_cli_dispatches_convert_with_output_dir(monkeypatch) -> None:
    calls: list[str] = []

    def fake_convert(options):
        calls.append("convert")
        return _result("convert", output_path=Path("converted.docx"))

    monkeypatch.setattr(phase1_cli, "convert", fake_convert)

    assert phase1_cli.main(["--output-dir", "out"]) == 0
    assert calls == ["convert"]


def test_cli_dispatches_analyze_without_output_dir_or_apply_review(monkeypatch) -> None:
    calls: list[str] = []

    def fake_analyze(options):
        calls.append("analyze")
        return _result("analyze")

    monkeypatch.setattr(phase1_cli, "analyze", fake_analyze)

    assert phase1_cli.main(["--input", "input.docx"]) == 0
    assert calls == ["analyze"]


def test_cli_returns_1_for_schema_errors(monkeypatch, capsys) -> None:
    def fake_analyze(options):
        return _result("analyze", errors=[ErrorRecord(code="INPUT_NOT_FOUND", message="missing")])

    monkeypatch.setattr(phase1_cli, "analyze", fake_analyze)

    assert phase1_cli.main([]) == 1
    captured = capsys.readouterr()
    assert "錯誤：INPUT_NOT_FOUND missing" in captured.err


def test_cli_candidate_failures_do_not_return_1(monkeypatch) -> None:
    apply_result = SimpleNamespace(applied_count=0, skipped_count=1, failed_count=1)

    def fake_apply_review(options):
        result = _result("apply_review", output_path=Path("reviewed.docx"))
        return Phase1StubResult(
            operation=result.operation,
            config_check=result.config_check,
            schema=result.schema,
            message=result.message,
            docx_processed=result.docx_processed,
            output_path=result.output_path,
            apply_result=apply_result,
        )

    monkeypatch.setattr(phase1_cli, "apply_review", fake_apply_review)

    assert phase1_cli.main(["--apply-review", "review.json"]) == 0


def test_cli_unexpected_exception_returns_1(monkeypatch, capsys) -> None:
    def fake_analyze(options):
        raise RuntimeError("boom")

    monkeypatch.setattr(phase1_cli, "analyze", fake_analyze)

    assert phase1_cli.main([]) == 1
    assert "錯誤：發生未預期錯誤。" in capsys.readouterr().err


def test_cli_stdout_summary_by_mode(monkeypatch, capsys) -> None:
    def fake_analyze(options):
        return _result("analyze")

    monkeypatch.setattr(phase1_cli, "analyze", fake_analyze)

    assert phase1_cli.main([]) == 0
    assert capsys.readouterr().out.splitlines() == [
        "模式：analyze",
        "章節候選數：0",
        "高風險候選數：0",
        "段落合併候選數：0",
    ]


def test_cli_unknown_argument_exits_2() -> None:
    with pytest.raises(SystemExit) as exc:
        phase1_cli.main(["--unknown"])
    assert exc.value.code == 2


def test_cli_writes_json_and_txt_reports(monkeypatch, tmp_path) -> None:
    def fake_analyze(options):
        return _result("analyze")

    monkeypatch.setattr(phase1_cli, "analyze", fake_analyze)
    json_path = tmp_path / "report.json"
    txt_path = tmp_path / "report.txt"

    assert phase1_cli.main(["--json-report", str(json_path), "--txt-report", str(txt_path)]) == 0

    assert json_path.exists()
    assert txt_path.exists()


def test_cli_report_write_error_returns_1(monkeypatch, capsys) -> None:
    def fake_analyze(options):
        return _result("analyze")

    def fake_write_reports(result, json_report_path, txt_report_path):
        return ReportWriteResult(
            json_report_path=None,
            txt_report_path=None,
            errors=[ErrorRecord(code="REPORT_JSON_WRITE_FAILED", message="無法寫入報告檔：report.json")],
        )

    monkeypatch.setattr(phase1_cli, "analyze", fake_analyze)
    monkeypatch.setattr(phase1_cli, "write_phase1_reports", fake_write_reports)

    assert phase1_cli.main(["--json-report", "report.json"]) == 1
    assert "錯誤：REPORT_JSON_WRITE_FAILED 無法寫入報告檔：report.json" in capsys.readouterr().err
