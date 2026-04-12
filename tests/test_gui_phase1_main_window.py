import os
from pathlib import Path
from types import SimpleNamespace

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication, QMessageBox

import src.gui.main_window_clean as main_window_clean
from src.gui.main_window_clean import MainWindow
from src.review_schema import ErrorRecord, ReviewSchema, TocState


@pytest.fixture
def qt_app():
    app = QApplication.instance() or QApplication([])
    return app


@pytest.fixture
def window(qt_app):
    window = MainWindow()
    yield window
    window.close()


def _set_phase1_operation(window: MainWindow, operation: str) -> None:
    index = window.phase1_operation_combo.findData(operation)
    assert index >= 0
    window.phase1_operation_combo.setCurrentIndex(index)


def _patch_message_boxes(monkeypatch):
    warnings = []
    criticals = []
    monkeypatch.setattr(QMessageBox, "warning", lambda *args: warnings.append(args))
    monkeypatch.setattr(QMessageBox, "critical", lambda *args: criticals.append(args))
    return warnings, criticals


def test_phase1_main_window_analyze_builds_request(monkeypatch, window) -> None:
    received = []
    expected = SimpleNamespace(
        operation="analyze",
        schema=ReviewSchema(chapter_candidates=[object()], review_candidates=[object(), object()]),
        config_check=SimpleNamespace(warnings=["設定警告"]),
        output_path=None,
        apply_result=None,
    )

    def fake_run(request):
        received.append(request)
        return expected

    monkeypatch.setattr(main_window_clean.phase1_worker, "run_phase1_gui_request", fake_run)

    _set_phase1_operation(window, "analyze")
    window.phase1_input_edit.setText("novel.docx")
    window.phase1_config_edit.setText("config.yaml")
    window.phase1_profile_edit.setText("default")

    window._run_phase1()

    assert received
    assert received[0].operation == "analyze"
    assert received[0].input_path == Path("novel.docx")
    assert received[0].config_path == Path("config.yaml")
    assert received[0].profile == "default"
    assert received[0].output_dir is None
    assert "章節候選數=1" in window.phase1_result_label.text()
    assert "高風險候選數=2" in window.phase1_result_label.text()
    assert "設定警告數=1" in window.phase1_result_label.text()


def test_phase1_main_window_convert_requires_output_dir(monkeypatch, window) -> None:
    warnings, _criticals = _patch_message_boxes(monkeypatch)
    calls = []
    monkeypatch.setattr(
        main_window_clean.phase1_worker,
        "run_phase1_gui_request",
        lambda request: calls.append(request),
    )

    _set_phase1_operation(window, "convert")
    window.phase1_input_edit.setText("novel.docx")
    window.phase1_output_dir_edit.clear()

    window._run_phase1()

    assert calls == []
    assert warnings
    assert "輸出資料夾" in window.phase1_error_label.text()


def test_phase1_main_window_apply_review_requires_review_json(monkeypatch, window) -> None:
    warnings, _criticals = _patch_message_boxes(monkeypatch)
    calls = []
    monkeypatch.setattr(
        main_window_clean.phase1_worker,
        "run_phase1_gui_request",
        lambda request: calls.append(request),
    )

    _set_phase1_operation(window, "apply_review")
    window.phase1_input_edit.setText("converted.docx")
    window.phase1_output_dir_edit.setText("out")
    window.phase1_apply_review_edit.clear()

    window._run_phase1()

    assert calls == []
    assert warnings
    assert "reviewed JSON" in window.phase1_error_label.text()


def test_phase1_main_window_apply_review_passes_reviewed_output(monkeypatch, window) -> None:
    received = []
    apply_result = SimpleNamespace(applied_count=2, skipped_count=1, failed_count=0)
    expected = SimpleNamespace(
        operation="apply_review",
        schema=ReviewSchema(),
        config_check=SimpleNamespace(warnings=["設定警告"]),
        output_path=Path("reviewed.docx"),
        apply_result=apply_result,
    )

    def fake_run(request):
        received.append(request)
        return expected

    monkeypatch.setattr(main_window_clean.phase1_worker, "run_phase1_gui_request", fake_run)

    _set_phase1_operation(window, "apply_review")
    window.phase1_input_edit.setText("converted.docx")
    window.phase1_apply_review_edit.setText("reviewed.json")
    window.phase1_output_dir_edit.clear()
    window.phase1_reviewed_output_edit.setText("reviewed.docx")

    window._run_phase1()

    assert received
    assert received[0].operation == "apply_review"
    assert received[0].input_path == Path("converted.docx")
    assert received[0].apply_review_path == Path("reviewed.json")
    assert received[0].reviewed_output_path == Path("reviewed.docx")
    assert received[0].output_dir is None
    assert "套用數=2" in window.phase1_result_label.text()
    assert "略過數=1" in window.phase1_result_label.text()
    assert "失敗數=0" in window.phase1_result_label.text()
    assert "設定警告數=1" in window.phase1_result_label.text()


def test_phase1_main_window_convert_summary(monkeypatch, window) -> None:
    expected = SimpleNamespace(
        operation="convert",
        schema=ReviewSchema(review_candidates=[object(), object(), object()]),
        config_check=SimpleNamespace(warnings=[]),
        output_path=Path("converted.docx"),
        apply_result=None,
    )
    monkeypatch.setattr(main_window_clean.phase1_worker, "run_phase1_gui_request", lambda request: expected)

    _set_phase1_operation(window, "convert")
    window.phase1_input_edit.setText("novel.docx")
    window.phase1_output_dir_edit.setText("out")

    window._run_phase1()

    assert "輸出檔案=converted.docx" in window.phase1_result_label.text()
    assert "高風險候選數=3" in window.phase1_result_label.text()
    assert "錯誤數=0" in window.phase1_result_label.text()


def test_phase1_main_window_analyze_shows_default_toc_status(monkeypatch, window) -> None:
    expected = SimpleNamespace(
        operation="analyze",
        schema=ReviewSchema(toc=TocState()),
        config_check=SimpleNamespace(warnings=[]),
        output_path=None,
        apply_result=None,
    )
    monkeypatch.setattr(main_window_clean.phase1_worker, "run_phase1_gui_request", lambda request: expected)

    _set_phase1_operation(window, "analyze")
    window.phase1_input_edit.setText("novel.docx")

    window._run_phase1()

    text = window.phase1_result_label.text()
    assert "TOC 狀態：not_requested" in text
    assert "TOC fallback：否" in text
    assert "TOC 章節數：0" in text


def test_phase1_main_window_convert_shows_toc_status(monkeypatch, window) -> None:
    expected = SimpleNamespace(
        operation="convert",
        schema=ReviewSchema(toc=TocState(requested=True, status="field_inserted", chapter_count=2)),
        config_check=SimpleNamespace(warnings=[]),
        output_path=Path("converted.docx"),
        apply_result=None,
    )
    monkeypatch.setattr(main_window_clean.phase1_worker, "run_phase1_gui_request", lambda request: expected)

    _set_phase1_operation(window, "convert")
    window.phase1_input_edit.setText("novel.docx")
    window.phase1_output_dir_edit.setText("out")

    window._run_phase1()

    text = window.phase1_result_label.text()
    assert "TOC 狀態：field_inserted" in text
    assert "TOC fallback：否" in text
    assert "TOC 章節數：2" in text


def test_phase1_main_window_apply_review_shows_toc_fallback_status(monkeypatch, window) -> None:
    apply_result = SimpleNamespace(applied_count=1, skipped_count=0, failed_count=0)
    expected = SimpleNamespace(
        operation="apply_review",
        schema=ReviewSchema(
            toc=TocState(requested=True, status="fallback_chapter_list", fallback_used=True, chapter_count=3)
        ),
        config_check=SimpleNamespace(warnings=[]),
        output_path=Path("reviewed.docx"),
        apply_result=apply_result,
    )
    monkeypatch.setattr(main_window_clean.phase1_worker, "run_phase1_gui_request", lambda request: expected)

    _set_phase1_operation(window, "apply_review")
    window.phase1_input_edit.setText("converted.docx")
    window.phase1_apply_review_edit.setText("reviewed.json")
    window.phase1_output_dir_edit.setText("out")

    window._run_phase1()

    text = window.phase1_result_label.text()
    assert "TOC 狀態：fallback_chapter_list" in text
    assert "TOC fallback：是" in text
    assert "TOC 章節數：3" in text


def test_phase1_main_window_does_not_add_toc_controls(window) -> None:
    assert not hasattr(window, "phase1_create_toc_var")
    assert not hasattr(window, "phase1_create_toc_checkbox")
    assert not hasattr(window, "phase1_create_toc_button")


def test_phase1_main_window_shows_first_schema_error(monkeypatch, window) -> None:
    expected = SimpleNamespace(
        operation="analyze",
        schema=ReviewSchema(errors=[ErrorRecord(code="INPUT_NOT_FOUND", message="找不到輸入 DOCX。")]),
        config_check=SimpleNamespace(warnings=[]),
        output_path=None,
        apply_result=None,
    )
    monkeypatch.setattr(main_window_clean.phase1_worker, "run_phase1_gui_request", lambda request: expected)

    _set_phase1_operation(window, "analyze")
    window.phase1_input_edit.setText("missing.docx")

    window._run_phase1()

    assert "錯誤數=1" in window.phase1_result_label.text()
    assert "INPUT_NOT_FOUND 找不到輸入 DOCX。" in window.phase1_error_label.text()


def test_phase1_main_window_unexpected_error_hides_traceback(monkeypatch, window) -> None:
    _warnings, criticals = _patch_message_boxes(monkeypatch)

    def fake_run(_request):
        raise RuntimeError("boom")

    monkeypatch.setattr(main_window_clean.phase1_worker, "run_phase1_gui_request", fake_run)

    _set_phase1_operation(window, "analyze")
    window.phase1_input_edit.setText("novel.docx")

    window._run_phase1()

    assert criticals
    assert "Phase 1 執行失敗" in window.phase1_result_label.text()
    assert "boom" in window.phase1_error_label.text()
    assert "Traceback" not in window.phase1_error_label.text()
