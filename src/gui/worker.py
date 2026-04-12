from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from PySide6.QtCore import QObject, Signal, Slot

from src.processing_service_v3 import (
    ApplyReviewOptions,
    ProcessingOptions,
    ProgressUpdate,
    run_apply_review,
    run_processing,
)


@dataclass(frozen=True)
class GuiRunRequest:
    output_dir: Path
    mode: str = "process"
    apply_review_summary_path: Path | None = None
    input_file: Path | None = None
    input_dir: Path | None = None
    recursive: bool = False
    config_path: Path | None = None
    term_dict_path: Path | None = None
    high_risk_rules_path: Path | None = None
    report_name: str | None = None
    format_overrides: dict[str, Any] | None = None
    profile: str | None = None


class ProcessingWorker(QObject):
    progress = Signal(int, int, str)
    success = Signal(dict)
    error = Signal(str)
    finished = Signal()

    def __init__(self, request: GuiRunRequest) -> None:
        super().__init__()
        self._request = request

    @Slot()
    def run(self) -> None:
        try:
            if self._request.mode == "apply_review":
                if self._request.apply_review_summary_path is None:
                    raise ValueError("未提供待套用的 review_summary 檔案。")
                result = run_apply_review(
                    ApplyReviewOptions(
                        output_dir=self._request.output_dir,
                        apply_review_summary_path=self._request.apply_review_summary_path,
                        input_file=self._request.input_file,
                        input_dir=self._request.input_dir,
                        recursive=self._request.recursive,
                        config_path=self._request.config_path,
                        format_overrides=self._request.format_overrides,
                        profile=self._request.profile,
                    ),
                    progress_callback=self._on_progress,
                )
                reviewed_file = str(result.output_files[0]) if result.output_files else ""
                self.success.emit(
                    {
                        "mode": "apply_review",
                        "total_candidates": result.total_candidates,
                        "applied_count": result.applied_count,
                        "skipped_count": result.skipped_count,
                        "not_found_count": result.not_found_count,
                        "conflict_count": result.conflict_count,
                        "failed_count": result.failed_count,
                        "failure_count": result.failure_count,
                        "reason_counts": result.reason_counts,
                        "apply_summary_path": str(result.apply_summary_path),
                        "reviewed_file_path": reviewed_file,
                        "output_dir": str(self._request.output_dir),
                    }
                )
            else:
                result = run_processing(
                    ProcessingOptions(
                        output_dir=self._request.output_dir,
                        input_file=self._request.input_file,
                        input_dir=self._request.input_dir,
                        recursive=self._request.recursive,
                        config_path=self._request.config_path,
                        term_dict_path=self._request.term_dict_path,
                        high_risk_rules_path=self._request.high_risk_rules_path,
                        report_name=self._request.report_name,
                        format_overrides=self._request.format_overrides,
                        profile=self._request.profile,
                    ),
                    progress_callback=self._on_progress,
                )
                self.success.emit(
                    {
                        "mode": "process",
                        "success_count": result.success_count,
                        "failure_count": result.failure_count,
                        "total_replacements": result.total_replacements,
                        "total_review_candidates": result.total_review_candidates,
                        "total_anomalies": result.total_anomalies,
                        "report_path": str(result.report_path),
                        "review_summary_path": str(result.review_summary_path),
                        "review_category_counts": result.review_category_counts,
                        "top_risk_files": result.top_risk_files,
                        "low_risk_rules_path": str(result.low_risk_rules_path),
                        "high_risk_rules_path": str(result.high_risk_rules_path),
                        "active_low_risk_rule_count": result.active_low_risk_rule_count,
                        "active_high_risk_rule_count": result.active_high_risk_rule_count,
                        "active_config_path": str(result.active_config_path) if result.active_config_path else "",
                        "active_profile": result.active_profile,
                        "available_profiles": result.available_profiles,
                        "output_dir": str(self._request.output_dir),
                    }
                )
        except Exception as exc:
            self.error.emit(str(exc))
        finally:
            self.finished.emit()

    def _on_progress(self, update: ProgressUpdate) -> None:
        self.progress.emit(update.current, update.total, update.message)
