from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from src.batch_runner import BatchRunResult, collect_input_files, process_single_file, run_batch
from src.config_loader import apply_format_overrides, load_config
from src.converter import OpenCCConverter
from src.replacer import (
    filter_out_high_risk_terms,
    normalize_terms_with_converter,
)
from src.review_apply import apply_review_decisions
from src.report_writer import write_report
from src.risk_terms import DEFAULT_HIGH_RISK_RULES, DEFAULT_HIGH_RISK_RULES_PATH
from src.rule_loader import (
    build_high_risk_category_map,
    build_high_risk_suggestion_map,
    build_high_risk_term_list,
    build_low_risk_mapping,
    load_high_risk_rules,
    load_low_risk_rules,
)


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
    high_risk_rules_path: Path | None = None
    report_name: str | None = None
    format_overrides: dict[str, Any] | None = None
    profile: str | None = None


@dataclass(frozen=True)
class ApplyReviewOptions:
    output_dir: Path
    apply_review_summary_path: Path
    input_file: Path | None = None
    input_dir: Path | None = None
    recursive: bool = False
    config_path: Path | None = None
    format_overrides: dict[str, Any] | None = None
    profile: str | None = None


@dataclass(frozen=True)
class ProcessingResult:
    file_paths: list[Path]
    batch_result: BatchRunResult
    report_path: Path
    review_summary_path: Path
    success_count: int
    failure_count: int
    total_replacements: int
    total_review_candidates: int
    total_anomalies: int
    review_category_counts: dict[str, int]
    top_risk_files: list[tuple[str, int]]
    low_risk_rules_path: Path
    high_risk_rules_path: Path
    active_low_risk_rule_count: int
    active_high_risk_rule_count: int
    active_config_path: Path | None
    active_profile: str
    available_profiles: list[str]


@dataclass(frozen=True)
class ApplyReviewResult:
    file_paths: list[Path]
    output_files: list[Path]
    apply_summary_path: Path
    total_candidates: int
    applied_count: int
    skipped_count: int
    not_found_count: int
    conflict_count: int
    failed_count: int
    failure_count: int
    reason_counts: dict[str, int]


ProgressCallback = Callable[[ProgressUpdate], None]


def run_processing(
    options: ProcessingOptions,
    progress_callback: ProgressCallback | None = None,
) -> ProcessingResult:
    output_dir = options.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    config = load_config(
        options.config_path.resolve() if options.config_path else None,
        profile_name=options.profile,
    )
    active_config_path = options.config_path.resolve() if options.config_path else None
    active_document_format = apply_format_overrides(config.document_format, options.format_overrides)
    report_name = options.report_name if options.report_name else config.default_report_name
    low_risk_rules_path = (
        options.term_dict_path.resolve() if options.term_dict_path else config.default_term_dict_path
    )
    high_risk_rules_path = (
        options.high_risk_rules_path.resolve()
        if options.high_risk_rules_path
        else config.default_high_risk_rules_path
    )

    file_paths = collect_input_files(
        input_file=options.input_file.resolve() if options.input_file else None,
        input_dir=options.input_dir.resolve() if options.input_dir else None,
        recursive=bool(options.recursive),
    )
    if not file_paths:
        raise FileNotFoundError("找不到可處理的 .docx 檔案。")

    converter = OpenCCConverter(config.opencc_config)
    low_risk_rules = load_low_risk_rules(low_risk_rules_path)
    raw_term_mapping = build_low_risk_mapping(low_risk_rules)
    term_mapping = normalize_terms_with_converter(raw_term_mapping, converter)
    if high_risk_rules_path.exists():
        high_risk_rules = load_high_risk_rules(high_risk_rules_path)
    else:
        using_explicit_path = options.high_risk_rules_path is not None
        configured_default_missing = (
            config.default_high_risk_rules_path.resolve() != DEFAULT_HIGH_RISK_RULES_PATH.resolve()
        )
        if using_explicit_path or configured_default_missing:
            raise FileNotFoundError(f"找不到高風險規則檔案：{high_risk_rules_path}")
        high_risk_rules = DEFAULT_HIGH_RISK_RULES
    high_risk_terms = build_high_risk_term_list(high_risk_rules)
    high_risk_category_map = build_high_risk_category_map(high_risk_rules)
    high_risk_suggestion_map = build_high_risk_suggestion_map(high_risk_rules)

    term_mapping = filter_out_high_risk_terms(
        term_mapping=term_mapping,
        high_risk_terms=high_risk_terms,
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
                    message=f"處理中：{file_path.name}",
                )
            )
        try:
            return process_single_file(
                file_path=file_path,
                output_dir=output_dir,
                converter=converter,
                term_mapping=term_mapping,
                enable_space_cleanup=config.enable_space_cleanup,
                document_format=active_document_format,
                high_risk_terms=high_risk_terms,
                high_risk_category_map=high_risk_category_map,
                high_risk_suggestion_map=high_risk_suggestion_map,
            )
        finally:
            completed += 1
            if progress_callback:
                progress_callback(
                    ProgressUpdate(
                        current=completed,
                        total=total_files,
                        file_name=file_path.name,
                        message=f"已完成：{file_path.name}",
                    )
                )

    batch_result = run_batch(file_paths=file_paths, processor=_processor)
    report_path = output_dir / report_name
    review_summary_path = write_report(
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
    review_category_counts = {
        "grammar": sum(item.review_grammar_count for item in batch_result.summaries),
        "wording": sum(item.review_wording_count for item in batch_result.summaries),
        "regional_usage": sum(item.review_regional_usage_count for item in batch_result.summaries),
    }

    file_risk_totals: dict[str, int] = {}
    for item in batch_result.review_candidates:
        file_risk_totals[item.file_name] = file_risk_totals.get(item.file_name, 0) + 1
    top_risk_files = sorted(file_risk_totals.items(), key=lambda kv: (-kv[1], kv[0]))[:5]

    return ProcessingResult(
        file_paths=file_paths,
        batch_result=batch_result,
        report_path=report_path,
        review_summary_path=review_summary_path,
        success_count=success_count,
        failure_count=failure_count,
        total_replacements=total_replacements,
        total_review_candidates=total_review_candidates,
        total_anomalies=total_anomalies,
        review_category_counts=review_category_counts,
        top_risk_files=top_risk_files,
        low_risk_rules_path=low_risk_rules_path,
        high_risk_rules_path=high_risk_rules_path
        if high_risk_rules_path.exists()
        else DEFAULT_HIGH_RISK_RULES_PATH,
        active_low_risk_rule_count=len([item for item in low_risk_rules if item.enabled and item.risk_level != "high"]),
        active_high_risk_rule_count=len(high_risk_terms),
        active_config_path=active_config_path,
        active_profile=config.active_profile,
        available_profiles=sorted(config.profiles.keys()),
    )


def run_apply_review(
    options: ApplyReviewOptions,
    progress_callback: ProgressCallback | None = None,
) -> ApplyReviewResult:
    output_dir = options.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    config = load_config(
        options.config_path.resolve() if options.config_path else None,
        profile_name=options.profile,
    )
    active_document_format = apply_format_overrides(config.document_format, options.format_overrides)

    file_paths = collect_input_files(
        input_file=options.input_file.resolve() if options.input_file else None,
        input_dir=options.input_dir.resolve() if options.input_dir else None,
        recursive=bool(options.recursive),
    )
    if not file_paths:
        raise FileNotFoundError("找不到可套用複核結果的 .docx 檔案。")

    if not options.apply_review_summary_path.exists():
        raise FileNotFoundError(f"找不到 review_summary 檔案: {options.apply_review_summary_path}")

    if progress_callback:
        progress_callback(
            ProgressUpdate(
                current=0,
                total=len(file_paths),
                file_name=options.apply_review_summary_path.name,
                message="載入人工複核清單中...",
            )
        )

    result = apply_review_decisions(
        source_files=file_paths,
        output_dir=output_dir,
        summary_path=options.apply_review_summary_path.resolve(),
        document_format=active_document_format,
    )

    if progress_callback:
        progress_callback(
            ProgressUpdate(
                current=len(file_paths),
                total=len(file_paths),
                file_name="",
                message="人工複核回填完成",
            )
        )

    return ApplyReviewResult(
        file_paths=file_paths,
        output_files=result.output_files,
        apply_summary_path=result.apply_summary_path,
        total_candidates=result.total_candidates,
        applied_count=result.applied_count,
        skipped_count=result.skipped_count,
        not_found_count=result.not_found_count,
        conflict_count=result.conflict_count,
        failed_count=result.failed_count,
        failure_count=len(result.failures),
        reason_counts=result.reason_counts,
    )
