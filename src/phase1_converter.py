from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from docx import Document

from src.converter import OpenCCConverter
from src.phase1_analyzer import analyze_docx
from src.phase1_config import Phase1ConfigCheck
from src.replacer import apply_replacements, filter_out_high_risk_terms, normalize_terms_with_converter
from src.review_schema import ErrorRecord, ReviewSchema
from src.rule_loader import build_high_risk_term_list, build_low_risk_mapping, load_high_risk_rules, load_low_risk_rules


@dataclass(frozen=True)
class ConvertDocxResult:
    schema: ReviewSchema
    output_path: Path | None
    converted: bool


def convert_docx(input_path: Path | None, output_dir: Path | None, config_check: Phase1ConfigCheck) -> ConvertDocxResult:
    if input_path is None:
        # Phase 1C intentionally keeps missing input path and missing file under INPUT_NOT_FOUND
        # to avoid expanding the public error-code contract in this narrowing pass.
        return _error_result("INPUT_NOT_FOUND", "未提供輸入檔。", "")
    schema = analyze_docx(input_path, config_check)
    if schema.errors:
        return ConvertDocxResult(schema=schema, output_path=None, converted=False)
    if output_dir is None:
        return _error_result("OUTPUT_DIR_REQUIRED", "未提供輸出資料夾。", "")

    try:
        output_dir.mkdir(parents=True, exist_ok=True)
    except Exception as exc:
        return _error_result("OUTPUT_DIR_CREATE_FAILED", f"無法建立輸出資料夾：{output_dir}", str(exc))

    try:
        document = Document(input_path)
    except Exception as exc:
        return _error_result("DOCX_READ_FAILED", f"無法讀取 DOCX：{input_path}", str(exc))

    converter = OpenCCConverter(config_check.config.opencc_config)
    low_risk_rules = load_low_risk_rules(config_check.config.default_term_dict_path)
    high_risk_rules = load_high_risk_rules(config_check.config.default_high_risk_rules_path)
    high_risk_terms = build_high_risk_term_list(high_risk_rules)
    term_mapping = build_low_risk_mapping(low_risk_rules)
    term_mapping = normalize_terms_with_converter(term_mapping, converter)
    term_mapping = filter_out_high_risk_terms(term_mapping, high_risk_terms, converter)
    high_risk_paragraphs = {candidate.paragraph_index for candidate in schema.review_candidates}

    for paragraph_index, paragraph in enumerate(document.paragraphs):
        converted_text = converter.convert(paragraph.text)
        if paragraph_index not in high_risk_paragraphs:
            converted_text, _, _ = apply_replacements(
                converted_text,
                paragraph_index=paragraph_index,
                term_mapping=term_mapping,
                file_name=input_path.name,
            )
        paragraph.text = converted_text

    output_path = _next_output_path(output_dir, input_path.stem)
    try:
        document.save(output_path)
    except Exception as exc:
        return _error_result("DOCX_WRITE_FAILED", f"無法寫入 converted DOCX：{output_path}", str(exc))

    return ConvertDocxResult(
        # Phase 1C keeps analysis-derived candidates in the schema.
        # Config compatibility warnings stay on config_check and are not copied into schema.warnings.
        schema=ReviewSchema(
            chapter_candidates=schema.chapter_candidates,
            review_candidates=schema.review_candidates,
            paragraph_merge_candidates=[],
            errors=[],
        ),
        output_path=output_path,
        converted=True,
    )


def _next_output_path(output_dir: Path, stem: str) -> Path:
    base = output_dir / f"{stem}_converted.docx"
    if not base.exists():
        return base
    index = 1
    while True:
        candidate = output_dir / f"{stem}_converted_{index:03d}.docx"
        if not candidate.exists():
            return candidate
        index += 1


def _error_result(code: str, message: str, technical_detail: str) -> ConvertDocxResult:
    return ConvertDocxResult(
        schema=ReviewSchema(
            errors=[
                ErrorRecord(
                    code=code,
                    message=message,
                    technical_detail=technical_detail,
                )
            ]
        ),
        output_path=None,
        converted=False,
    )
