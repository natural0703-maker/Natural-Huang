from pathlib import Path

import pytest

from src.rule_loader import (
    build_high_risk_term_list,
    build_low_risk_mapping,
    load_high_risk_rules,
    load_low_risk_rules,
)
from tests.test_paths import make_test_dir


def test_low_risk_legacy_mapping_is_supported() -> None:
    tmp = make_test_dir("v35_low_legacy")
    path = tmp / "low.yaml"
    path.write_text('"软件": "軟體"\n', encoding="utf-8")

    rules = load_low_risk_rules(path)
    mapping = build_low_risk_mapping(rules)
    assert mapping == {"软件": "軟體"}


def test_low_risk_new_format_is_supported() -> None:
    tmp = make_test_dir("v35_low_new")
    path = tmp / "low.yaml"
    path.write_text(
        "- source: 软件\n"
        "  target: 軟體\n"
        "  risk_level: low\n"
        "  enabled: true\n"
        "  category: tech\n"
        "  note: keep\n"
        "- source: 文档\n"
        "  target: 文件\n"
        "  enabled: false\n",
        encoding="utf-8",
    )

    rules = load_low_risk_rules(path)
    mapping = build_low_risk_mapping(rules)
    assert mapping == {"软件": "軟體"}


def test_high_risk_rules_enabled_false_is_ignored() -> None:
    tmp = make_test_dir("v35_high_enabled")
    path = tmp / "high.yaml"
    path.write_text(
        "- term: 支持\n"
        "  risk_category: wording\n"
        "  enabled: false\n"
        "  suggested_candidates: 建議改為支援\n"
        "- term: 資訊\n"
        "  risk_category: wording\n"
        "  enabled: true\n"
        "  suggested_candidates: 請人工確認\n",
        encoding="utf-8",
    )

    rules = load_high_risk_rules(path)
    terms = build_high_risk_term_list(rules)
    assert "資訊" in terms
    assert "支持" not in terms


def test_rule_missing_required_fields_raises_error() -> None:
    tmp = make_test_dir("v35_missing_fields")
    low_path = tmp / "low.yaml"
    high_path = tmp / "high.yaml"
    low_path.write_text("- source: 软件\n", encoding="utf-8")
    high_path.write_text("- risk_category: wording\n", encoding="utf-8")

    with pytest.raises(ValueError):
        load_low_risk_rules(low_path)
    with pytest.raises(ValueError):
        load_high_risk_rules(high_path)


def test_duplicate_enabled_rule_raises_error() -> None:
    tmp = make_test_dir("v35_duplicate_rules")
    low_path = tmp / "low.yaml"
    high_path = tmp / "high.yaml"
    low_path.write_text(
        "- source: 软件\n"
        "  target: 軟體\n"
        "- source: 软件\n"
        "  target: 軟件\n",
        encoding="utf-8",
    )
    high_path.write_text(
        "- term: 支持\n"
        "  risk_category: wording\n"
        "- term: 支持\n"
        "  risk_category: wording\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError):
        load_low_risk_rules(low_path)
    with pytest.raises(ValueError):
        load_high_risk_rules(high_path)
