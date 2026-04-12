from types import SimpleNamespace

import src.phase1_cli as phase1_cli
from docx import Document
from src.frozen_spec_v1 import HEADING_STYLE_NAME, OPENCC_DEFAULT
from src.phase1_config import load_phase1_config
from src.phase1_pipeline import Phase1Options, analyze, apply_review, convert
from src.review_schema import ReviewSchema


def _cli_fake_result(operation: str) -> SimpleNamespace:
    return SimpleNamespace(
        operation=operation,
        schema=ReviewSchema(),
        output_path=None,
        apply_result=None,
    )


def test_phase1_config_checks_frozen_values() -> None:
    result = load_phase1_config()

    assert result.config.opencc_config == OPENCC_DEFAULT
    assert result.config.document_format.heading_style_name == HEADING_STYLE_NAME
    assert result.low_risk_rule_count > 0
    assert result.high_risk_rule_count > 0
    assert any("24 pt" in warning for warning in result.warnings)


def test_pipeline_analyze_without_input_is_empty_and_apply_review_requires_input() -> None:
    result = analyze(Phase1Options())
    assert result.operation == "analyze"
    assert result.docx_processed is False
    assert result.schema.chapter_candidates == []
    assert result.schema.review_candidates == []
    assert result.schema.paragraph_merge_candidates == []
    assert result.schema.errors == []

    result = apply_review(Phase1Options())
    assert result.operation == "apply_review"
    assert result.docx_processed is False
    assert result.schema.errors
    assert result.schema.errors[0].code == "INPUT_NOT_FOUND"


def test_apply_review_without_review_json_returns_schema_error(tmp_path) -> None:
    source = tmp_path / "source.docx"
    Document().save(source)

    result = apply_review(Phase1Options(input_path=source, output_dir=tmp_path))

    assert result.operation == "apply_review"
    assert result.docx_processed is False
    assert result.schema.errors
    assert result.schema.errors[0].code == "REVIEW_JSON_NOT_FOUND"
    assert result.schema.chapter_candidates == []
    assert result.schema.review_candidates == []
    assert result.schema.paragraph_merge_candidates == []


def test_phase1_cli_dispatches_to_analyze_by_default(monkeypatch, capsys) -> None:
    calls: list[str] = []

    def fake_analyze(options):
        calls.append("analyze")
        return _cli_fake_result("analyze")

    monkeypatch.setattr(phase1_cli, "analyze", fake_analyze)

    assert phase1_cli.main([]) == 0
    assert calls == ["analyze"]
    capsys.readouterr()


def test_phase1_cli_dispatches_to_analyze_with_chapter_review_without_output_dir(monkeypatch) -> None:
    calls: list[str] = []

    def fake_analyze(options):
        calls.append("analyze")
        return _cli_fake_result("analyze")

    monkeypatch.setattr(phase1_cli, "analyze", fake_analyze)

    assert phase1_cli.main(["--chapter-review", "chapter_review.json"]) == 0
    assert calls == ["analyze"]


def test_phase1_cli_dispatches_to_apply_review_with_apply_review(monkeypatch) -> None:
    calls: list[str] = []

    def fake_apply_review(options):
        calls.append("apply_review")
        return _cli_fake_result("apply_review")

    monkeypatch.setattr(phase1_cli, "apply_review", fake_apply_review)

    assert phase1_cli.main(["--apply-review", "reviewed_input.json"]) == 0
    assert calls == ["apply_review"]
