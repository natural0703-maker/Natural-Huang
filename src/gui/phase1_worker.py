from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from src.phase1_pipeline import Phase1Options, analyze, apply_review, convert


SUPPORTED_PHASE1_GUI_OPERATIONS = {"analyze", "convert", "apply_review"}


@dataclass(frozen=True)
class Phase1GuiRequest:
    operation: str = "analyze"
    input_path: Path | None = None
    output_dir: Path | None = None
    config_path: Path | None = None
    profile: str | None = None
    apply_review_path: Path | None = None
    reviewed_output_path: Path | None = None


def run_phase1_gui_request(request: Phase1GuiRequest):
    if request.operation not in SUPPORTED_PHASE1_GUI_OPERATIONS:
        raise ValueError(f"不支援的 Phase 1 GUI 操作：{request.operation}")

    options = Phase1Options(
        input_path=request.input_path,
        output_dir=request.output_dir,
        config_path=request.config_path,
        profile=request.profile,
        apply_review_path=request.apply_review_path,
        reviewed_output_path=request.reviewed_output_path,
    )
    if request.operation == "analyze":
        return analyze(options)
    if request.operation == "convert":
        return convert(options)
    if request.operation == "apply_review":
        return apply_review(options)
    raise AssertionError("unreachable")
