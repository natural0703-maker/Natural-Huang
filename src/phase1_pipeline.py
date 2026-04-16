from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from src.phase1_analyzer import analyze_docx
from src.phase1_config import Phase1ConfigCheck, load_phase1_config
from src.phase1_converter import convert_docx
from src.phase1_review_apply import ReviewApplyResult, apply_review_docx
from src.review_schema import ReviewSchema


Phase1Operation = Literal["analyze", "convert", "apply_review"]


@dataclass(frozen=True)
class Phase1Options:
    input_path: Path | None = None
    output_dir: Path | None = None
    config_path: Path | None = None
    profile: str | None = None
    create_toc: bool = True
    enable_line_break_cleanup: bool = False
    chapter_page_break: bool = False
    chapter_review_path: Path | None = None
    json_report_path: Path | None = None
    txt_report_path: Path | None = None
    apply_review_path: Path | None = None
    reviewed_output_path: Path | None = None


@dataclass(frozen=True)
class Phase1StubResult:
    operation: Phase1Operation
    config_check: Phase1ConfigCheck
    schema: ReviewSchema
    message: str
    docx_processed: bool = False
    output_path: Path | None = None
    apply_result: ReviewApplyResult | None = None


def analyze(options: Phase1Options) -> Phase1StubResult:
    config_check = load_phase1_config(options.config_path, options.profile)
    if options.input_path is None:
        return Phase1StubResult(
            operation="analyze",
            config_check=config_check,
            schema=ReviewSchema(),
            message="Phase 1B analyze：未提供輸入檔，已回傳空 schema。",
            docx_processed=False,
        )

    schema = analyze_docx(options.input_path, config_check)
    message = (
        "Phase 1B analyze：分析未完成，請查看 schema.errors。"
        if schema.errors
        else "Phase 1B analyze：只讀分析完成。"
    )
    return Phase1StubResult(
        operation="analyze",
        config_check=config_check,
        schema=schema,
        message=message,
        docx_processed=False,
    )


def convert(options: Phase1Options) -> Phase1StubResult:
    config_check = load_phase1_config(options.config_path, options.profile)
    result = convert_docx(
        options.input_path,
        options.output_dir,
        config_check,
        create_toc=options.create_toc,
        enable_line_break_cleanup=options.enable_line_break_cleanup,
    )
    message = (
        "Phase 1C convert：已輸出 converted DOCX。"
        if result.converted
        else "Phase 1C convert：轉換未完成，請查看 schema.errors。"
    )
    return Phase1StubResult(
        operation="convert",
        config_check=config_check,
        schema=result.schema,
        message=message,
        docx_processed=result.converted,
        output_path=result.output_path,
    )


def apply_review(options: Phase1Options) -> Phase1StubResult:
    config_check = load_phase1_config(options.config_path, options.profile)
    result = apply_review_docx(
        options.input_path,
        options.apply_review_path,
        options.output_dir,
        options.reviewed_output_path,
        create_toc=options.create_toc,
    )
    message = (
        "Phase 1D apply_review：已輸出 reviewed DOCX。"
        if result.output_path is not None
        else "Phase 1D apply_review：回填未完成，請查看 schema.errors。"
    )
    return Phase1StubResult(
        operation="apply_review",
        config_check=config_check,
        schema=result.schema,
        message=message,
        docx_processed=result.output_path is not None,
        output_path=result.output_path,
        apply_result=result,
    )


def _stub(operation: Phase1Operation, options: Phase1Options, message: str) -> Phase1StubResult:
    return Phase1StubResult(
        operation=operation,
        config_check=load_phase1_config(options.config_path, options.profile),
        schema=ReviewSchema(),
        message=message,
        docx_processed=False,
    )
