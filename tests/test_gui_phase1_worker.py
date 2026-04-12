from pathlib import Path
from types import SimpleNamespace

import pytest

import src.gui.phase1_worker as phase1_worker
from src.gui.phase1_worker import Phase1GuiRequest, run_phase1_gui_request


def test_phase1_gui_worker_calls_analyze_and_returns_pipeline_result(monkeypatch) -> None:
    received = []
    expected = SimpleNamespace(operation="analyze")

    def fake_analyze(options):
        received.append(options)
        return expected

    monkeypatch.setattr(phase1_worker, "analyze", fake_analyze)

    result = run_phase1_gui_request(
        Phase1GuiRequest(
            operation="analyze",
            input_path=Path("input.docx"),
            config_path=Path("config.yaml"),
            profile="default",
        )
    )

    assert result is expected
    assert received[0].input_path == Path("input.docx")
    assert received[0].config_path == Path("config.yaml")
    assert received[0].profile == "default"
    assert received[0].output_dir is None
    assert received[0].apply_review_path is None
    assert received[0].reviewed_output_path is None


def test_phase1_gui_worker_calls_convert_and_returns_pipeline_result(monkeypatch) -> None:
    received = []
    expected = SimpleNamespace(operation="convert")

    def fake_convert(options):
        received.append(options)
        return expected

    monkeypatch.setattr(phase1_worker, "convert", fake_convert)

    result = run_phase1_gui_request(
        Phase1GuiRequest(
            operation="convert",
            input_path=Path("input.docx"),
            output_dir=Path("out"),
            config_path=Path("config.yaml"),
        )
    )

    assert result is expected
    assert received[0].input_path == Path("input.docx")
    assert received[0].output_dir == Path("out")
    assert received[0].config_path == Path("config.yaml")


def test_phase1_gui_worker_calls_apply_review_and_returns_pipeline_result(monkeypatch) -> None:
    received = []
    expected = SimpleNamespace(operation="apply_review")

    def fake_apply_review(options):
        received.append(options)
        return expected

    monkeypatch.setattr(phase1_worker, "apply_review", fake_apply_review)

    result = run_phase1_gui_request(
        Phase1GuiRequest(
            operation="apply_review",
            input_path=Path("converted.docx"),
            output_dir=Path("out"),
            apply_review_path=Path("review.json"),
            reviewed_output_path=Path("reviewed.docx"),
        )
    )

    assert result is expected
    assert not isinstance(result, str)
    assert received[0].input_path == Path("converted.docx")
    assert received[0].output_dir == Path("out")
    assert received[0].apply_review_path == Path("review.json")
    assert received[0].reviewed_output_path == Path("reviewed.docx")


def test_phase1_gui_worker_rejects_unknown_operation() -> None:
    with pytest.raises(ValueError, match="不支援的 Phase 1 GUI 操作"):
        run_phase1_gui_request(Phase1GuiRequest(operation="unknown"))
