from pathlib import Path

from docx import Document

from src.processing_service_v3 import ProcessingOptions, run_processing
from tests.test_paths import make_test_dir


def _make_docx(path: Path, paragraphs: list[str]) -> None:
    doc = Document()
    for text in paragraphs:
        doc.add_paragraph(text)
    doc.save(str(path))


def test_custom_high_risk_rule_file_changes_replacement_behavior() -> None:
    tmp = make_test_dir("v35_custom_high_rules")
    input_file = tmp / "sample.docx"
    output_dir = tmp / "out"
    output_dir.mkdir(parents=True, exist_ok=True)

    term_dict = tmp / "low_rules.yaml"
    term_dict.write_text('"支持": "支援"\n', encoding="utf-8")
    _make_docx(input_file, ["我們支持這項計畫。"])

    result_default = run_processing(
        ProcessingOptions(
            input_file=input_file,
            output_dir=output_dir,
            term_dict_path=term_dict,
        )
    )
    assert result_default.total_replacements == 0

    custom_high_rules = tmp / "high_rules.yaml"
    custom_high_rules.write_text(
        "- term: 資訊\n"
        "  risk_category: wording\n"
        "  enabled: true\n"
        "  suggested_candidates: 請人工確認\n",
        encoding="utf-8",
    )
    result_custom = run_processing(
        ProcessingOptions(
            input_file=input_file,
            output_dir=output_dir,
            term_dict_path=term_dict,
            high_risk_rules_path=custom_high_rules,
        )
    )
    assert result_custom.total_replacements >= 1


def test_missing_custom_high_risk_rule_file_raises_error() -> None:
    tmp = make_test_dir("v35_missing_high_rules")
    input_file = tmp / "sample.docx"
    output_dir = tmp / "out"
    output_dir.mkdir(parents=True, exist_ok=True)
    _make_docx(input_file, ["測試內容"])

    missing = tmp / "missing_high.yaml"
    try:
        run_processing(
            ProcessingOptions(
                input_file=input_file,
                output_dir=output_dir,
                high_risk_rules_path=missing,
            )
        )
    except FileNotFoundError:
        return
    raise AssertionError("預期高風險規則檔不存在時應拋出 FileNotFoundError")


def test_processing_uses_rule_paths_from_config() -> None:
    tmp = make_test_dir("v35_rules_from_config")
    input_file = tmp / "sample.docx"
    output_dir = tmp / "out"
    output_dir.mkdir(parents=True, exist_ok=True)
    _make_docx(input_file, ["我們支持這項計畫。"])

    low_rules = tmp / "low.yaml"
    low_rules.write_text(
        "- source: 支持\n"
        "  target: 支援\n"
        "  risk_level: low\n"
        "  enabled: true\n"
        "  category: wording\n"
        "  note: test\n",
        encoding="utf-8",
    )
    high_rules = tmp / "high.yaml"
    high_rules.write_text(
        "- term: 資訊\n"
        "  risk_category: wording\n"
        "  enabled: true\n"
        "  suggested_candidates: 請人工確認\n",
        encoding="utf-8",
    )
    config_path = tmp / "config.yaml"
    config_path.write_text(
        "opencc_config: s2t\n"
        "default_report_name: report.xlsx\n"
        "default_term_dict_path: low.yaml\n"
        "default_high_risk_rules_path: high.yaml\n"
        "enable_space_cleanup: true\n",
        encoding="utf-8",
    )

    result = run_processing(
        ProcessingOptions(
            input_file=input_file,
            output_dir=output_dir,
            config_path=config_path,
        )
    )
    assert result.total_replacements >= 1
    assert result.low_risk_rules_path.name == "low.yaml"
    assert result.high_risk_rules_path.name == "high.yaml"
