from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from src.batch_runner import BatchRunResult, collect_input_files, process_single_file, run_batch
from src.config_loader import load_config
from src.converter import OpenCCConverter
from src.replacer import (
    filter_out_high_risk_terms,
    load_term_dict,
    normalize_terms_with_converter,
)
from src.report_writer import write_report
from src.risk_terms import HIGH_RISK_TERMS


@dataclass(frozen=True)
class ProgressUpdate:
    current: int
    total: int
    file_name: str
    message: str


@dataclass(frozen=True)
class ProcessingOptions:
    output_dir: Path
    input_file: Path | None = None
    input_dir: Path | None = None
    recursive: bool = False
    config_path: Path | None = None
    term_dict_path: Path | None = None
    report_name: str | None = None


@dataclass(frozen=True)
class ProcessingResult:
    file_paths: list[Path]
    batch_result: BatchRunResult
    report_path: Path
    success_count: int
    failure_count: int
    total_replacements: int


ProgressCallback = Callable[[ProgressUpdate], None]


def run_processing(
    options: ProcessingOptions,
    progress_callback: ProgressCallback | None = None,
) -> ProcessingResult:
    output_dir = options.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    config = load_config(options.config_path.resolve() if options.config_path else None)
    report_name = options.report_name if options.report_name else config.default_report_name
    term_dict_path = (
        options.term_dict_path.resolve() if options.term_dict_path else config.default_term_dict_path
    )

    file_paths = collect_input_files(
        input_file=options.input_file.resolve() if options.input_file else None,
        input_dir=options.input_dir.resolve() if options.input_dir else None,
        recursive=bool(options.recursive),
    )
    if not file_paths:
        raise FileNotFoundError("找不到可處理的 .docx 檔案。")

    converter = OpenCCConverter(config.opencc_config)
    raw_term_mapping = load_term_dict(term_dict_path)
    term_mapping = normalize_terms_with_converter(raw_term_mapping, converter)
    term_mapping = filter_out_high_risk_terms(
        term_mapping=term_mapping,
        high_risk_terms=HIGH_RISK_TERMS,
        converter=converter,
    )

    total_files = len(file_paths)
    completed = 0

    def _processor(file_path: Path):
        nonlocal completed
        if progress_callback:
            progress_callback(
                ProgressUpdate(
                    current=completed,
                    total=total_files,
                    file_name=file_path.name,
                    message=f"開始處理：{file_path.name}",
                )
            )
        try:
            return process_single_file(
                file_path=file_path,
                output_dir=output_dir,
                converter=converter,
                term_mapping=term_mapping,
                enable_space_cleanup=config.enable_space_cleanup,
            )
        finally:
            completed += 1
            if progress_callback:
                progress_callback(
                    ProgressUpdate(
                        current=completed,
                        total=total_files,
                        file_name=file_path.name,
                        message=f"完成處理：{file_path.name}",
                    )
                )

    batch_result = run_batch(file_paths=file_paths, processor=_processor)
    report_path = output_dir / report_name
    write_report(
        report_path=report_path,
        summaries=batch_result.summaries,
        replacement_records=batch_result.replacements,
        review_candidates=batch_result.review_candidates,
        anomalies=batch_result.anomalies,
        failures=batch_result.failures,
    )

    success_count = sum(1 for item in batch_result.summaries if item.status == "success")
    failure_count = len(batch_result.failures)
    total_replacements = sum(item.total_replacements for item in batch_result.summaries)

    return ProcessingResult(
        file_paths=file_paths,
        batch_result=batch_result,
        report_path=report_path,
        success_count=success_count,
        failure_count=failure_count,
        total_replacements=total_replacements,
    )


# V3.0 override: enrich aggregate stats and normalize messages.
@dataclass(frozen=True)
class ProcessingResult:
    file_paths: list[Path]
    batch_result: BatchRunResult
    report_path: Path
    success_count: int
    failure_count: int
    total_replacements: int
    total_review_candidates: int
    total_anomalies: int


def run_processing(
    options: ProcessingOptions,
    progress_callback: ProgressCallback | None = None,
) -> ProcessingResult:
    output_dir = options.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    config = load_config(options.config_path.resolve() if options.config_path else None)
    report_name = options.report_name if options.report_name else config.default_report_name
    term_dict_path = (
        options.term_dict_path.resolve() if options.term_dict_path else config.default_term_dict_path
    )

    file_paths = collect_input_files(
        input_file=options.input_file.resolve() if options.input_file else None,
        input_dir=options.input_dir.resolve() if options.input_dir else None,
        recursive=bool(options.recursive),
    )
    if not file_paths:
        raise FileNotFoundError("找不到可處理的 .docx 檔案。")

    converter = OpenCCConverter(config.opencc_config)
    raw_term_mapping = load_term_dict(term_dict_path)
    term_mapping = normalize_terms_with_converter(raw_term_mapping, converter)
    term_mapping = filter_out_high_risk_terms(
        term_mapping=term_mapping,
        high_risk_terms=HIGH_RISK_TERMS,
        converter=converter,
    )

    total_files = len(file_paths)
    completed = 0

    def _processor(file_path: Path):
        nonlocal completed
        if progress_callback:
            progress_callback(
                ProgressUpdate(
                    current=completed,
                    total=total_files,
                    file_name=file_path.name,
                    message=f"開始處理：{file_path.name}",
                )
            )
        try:
            return process_single_file(
                file_path=file_path,
                output_dir=output_dir,
                converter=converter,
                term_mapping=term_mapping,
                enable_space_cleanup=config.enable_space_cleanup,
            )
        finally:
            completed += 1
            if progress_callback:
                progress_callback(
                    ProgressUpdate(
                        current=completed,
                        total=total_files,
                        file_name=file_path.name,
                        message=f"完成處理：{file_path.name}",
                    )
                )

    batch_result = run_batch(file_paths=file_paths, processor=_processor)
    report_path = output_dir / report_name
    write_report(
        report_path=report_path,
        summaries=batch_result.summaries,
        replacement_records=batch_result.replacements,
        review_candidates=batch_result.review_candidates,
        anomalies=batch_result.anomalies,
        failures=batch_result.failures,
    )

    success_count = sum(1 for item in batch_result.summaries if item.status == "success")
    failure_count = len(batch_result.failures)
    total_replacements = sum(item.total_replacements for item in batch_result.summaries)
    total_review_candidates = sum(item.total_review_candidates for item in batch_result.summaries)
    total_anomalies = sum(item.total_anomalies for item in batch_result.summaries)

    return ProcessingResult(
        file_paths=file_paths,
        batch_result=batch_result,
        report_path=report_path,
        success_count=success_count,
        failure_count=failure_count,
        total_replacements=total_replacements,
        total_review_candidates=total_review_candidates,
        total_anomalies=total_anomalies,
    )
