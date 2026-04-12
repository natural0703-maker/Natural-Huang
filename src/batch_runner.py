from __future__ import annotations

import time
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from src.anomaly_detector import detect_anomalies
from src.config_loader import DocumentFormatConfig
from src.converter import OpenCCConverter
from src.docx_reader import read_paragraphs
from src.docx_writer import ParagraphOutput, build_output_docx_path, write_paragraphs_to_docx
from src.heading_detector import is_direct_chapter_heading
from src.models import (
    AnomalyRecord,
    FailureRecord,
    ReplacementRecord,
    ReviewCandidateRecord,
    SummaryRecord,
)
from src.replacer import apply_replacements
from src.risk_detector import detect_high_risk_terms
from src.space_cleaner import clean_text_spacing


@dataclass(frozen=True)
class FileProcessResult:
    summary: SummaryRecord
    replacements: list[ReplacementRecord]
    review_candidates: list[ReviewCandidateRecord]
    anomalies: list[AnomalyRecord]


@dataclass(frozen=True)
class BatchRunResult:
    summaries: list[SummaryRecord]
    replacements: list[ReplacementRecord]
    review_candidates: list[ReviewCandidateRecord]
    anomalies: list[AnomalyRecord]
    failures: list[FailureRecord]


def collect_input_files(
    input_file: Path | None,
    input_dir: Path | None,
    recursive: bool,
) -> list[Path]:
    if (input_file is None and input_dir is None) or (input_file is not None and input_dir is not None):
        raise ValueError("參數錯誤：`--input-file/--input` 與 `--input-dir` 必須且只能提供其中一個。")

    if input_file is not None:
        resolved = input_file.resolve()
        if not resolved.exists():
            raise FileNotFoundError(f"找不到輸入檔案: {resolved}")
        if resolved.suffix.lower() != ".docx":
            raise ValueError(f"輸入檔案副檔名必須是 .docx: {resolved}")
        return [resolved]

    assert input_dir is not None
    resolved_dir = input_dir.resolve()
    if not resolved_dir.exists():
        raise FileNotFoundError(f"找不到輸入資料夾: {resolved_dir}")
    if not resolved_dir.is_dir():
        raise ValueError(f"輸入路徑不是資料夾: {resolved_dir}")

    if recursive:
        files = sorted(path for path in resolved_dir.rglob("*.docx") if path.is_file())
    else:
        files = sorted(path for path in resolved_dir.glob("*.docx") if path.is_file())
    return files


def process_single_file(
    file_path: Path,
    output_dir: Path,
    converter: OpenCCConverter,
    term_mapping: dict[str, str],
    enable_space_cleanup: bool,
    document_format: DocumentFormatConfig | None = None,
    high_risk_terms: list[str] | None = None,
    high_risk_category_map: dict[str, str] | None = None,
    high_risk_suggestion_map: dict[str, str] | None = None,
) -> FileProcessResult:
    start_time = time.perf_counter()
    source_paragraphs = read_paragraphs(file_path)

    output_paragraphs: list[ParagraphOutput] = []
    replacement_records: list[ReplacementRecord] = []
    review_candidates: list[ReviewCandidateRecord] = []
    anomalies: list[AnomalyRecord] = []
    total_replacements = 0
    current_chapter_guess = ""

    for index, paragraph_text in enumerate(source_paragraphs, start=1):
        converted = converter.convert(paragraph_text)
        replaced_text, records, replacement_count = apply_replacements(
            text=converted,
            paragraph_index=index,
            term_mapping=term_mapping,
            file_name=file_path.name,
        )
        final_text = clean_text_spacing(replaced_text) if enable_space_cleanup else replaced_text

        is_heading = is_direct_chapter_heading(final_text)
        if is_heading:
            current_chapter_guess = final_text.strip()

        review_candidates.extend(
            detect_high_risk_terms(
                text=final_text,
                paragraph_index=index,
                file_name=file_path.name,
                terms=high_risk_terms,
                category_map=high_risk_category_map,
                suggestion_map=high_risk_suggestion_map,
                original_text=paragraph_text,
                chapter_guess=current_chapter_guess,
            )
        )
        anomalies.extend(
            detect_anomalies(
                original_text=paragraph_text,
                converted_text=final_text,
                paragraph_index=index,
                file_name=file_path.name,
            )
        )

        output_paragraphs.append(
            ParagraphOutput(
                text=final_text,
                is_heading=is_heading,
            )
        )
        replacement_records.extend(records)
        total_replacements += replacement_count

    output_file_path = build_output_docx_path(file_path, output_dir)
    write_paragraphs_to_docx(
        output_paragraphs,
        output_file_path,
        document_format=document_format,
    )

    elapsed = time.perf_counter() - start_time
    review_counts = Counter(item.risk_category for item in review_candidates)
    summary = SummaryRecord(
        file_name=file_path.name,
        status="success",
        paragraph_count=len(source_paragraphs),
        total_replacements=total_replacements,
        total_review_candidates=len(review_candidates),
        total_anomalies=len(anomalies),
        elapsed_time_sec=round(elapsed, 4),
        review_grammar_count=review_counts.get("grammar", 0),
        review_wording_count=review_counts.get("wording", 0),
        review_regional_usage_count=review_counts.get("regional_usage", 0),
        output_file=str(output_file_path),
    )
    return FileProcessResult(
        summary=summary,
        replacements=replacement_records,
        review_candidates=review_candidates,
        anomalies=anomalies,
    )


def run_batch(
    file_paths: list[Path],
    processor: Callable[[Path], FileProcessResult],
) -> BatchRunResult:
    summaries: list[SummaryRecord] = []
    replacements: list[ReplacementRecord] = []
    review_candidates: list[ReviewCandidateRecord] = []
    anomalies: list[AnomalyRecord] = []
    failures: list[FailureRecord] = []

    for file_path in file_paths:
        try:
            result = processor(file_path)
            summaries.append(result.summary)
            replacements.extend(result.replacements)
            review_candidates.extend(result.review_candidates)
            anomalies.extend(result.anomalies)
        except Exception as exc:
            failures.append(
                FailureRecord(
                    file_name=file_path.name,
                    error_type=type(exc).__name__,
                    error_message=str(exc),
                )
            )
            summaries.append(
                SummaryRecord(
                    file_name=file_path.name,
                    status="failed",
                    paragraph_count=0,
                    total_replacements=0,
                    total_review_candidates=0,
                    total_anomalies=0,
                    elapsed_time_sec=0.0,
                    output_file="",
                )
            )

    return BatchRunResult(
        summaries=summaries,
        replacements=replacements,
        review_candidates=review_candidates,
        anomalies=anomalies,
        failures=failures,
    )
