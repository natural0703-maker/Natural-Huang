from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Any

import regex
import yaml

from src.models import ReplacementRecord
from src.rule_loader import build_low_risk_mapping, load_low_risk_rules


def _load_term_dict_legacy(path: Path) -> dict[str, str]:
    if not path.exists():
        raise FileNotFoundError(f"找不到詞庫檔案: {path}")

    with path.open("r", encoding="utf-8") as fh:
        raw_data: Any = yaml.safe_load(fh) or {}

    mapping: dict[str, str] = {}
    if isinstance(raw_data, dict):
        for source, target in raw_data.items():
            mapping[str(source)] = str(target)
    elif isinstance(raw_data, list):
        for item in raw_data:
            if not isinstance(item, dict):
                continue
            if "source" not in item or "target" not in item:
                continue

            enabled = item.get("enabled", True)
            if isinstance(enabled, str):
                enabled = enabled.lower() not in {"false", "0", "no"}
            if not bool(enabled):
                continue

            risk_level = str(item.get("risk_level", "low")).strip().lower()
            if risk_level == "high":
                continue

            mapping[str(item["source"])] = str(item["target"])

    normalized: dict[str, str] = {}
    for source, target in mapping.items():
        source_text = str(source).strip()
        target_text = str(target).strip()
        if source_text and target_text:
            normalized[source_text] = target_text

    return normalized


def normalize_terms_with_converter(
    term_mapping: dict[str, str],
    converter,
) -> dict[str, str]:
    normalized: dict[str, str] = {}
    for source_term, target_term in term_mapping.items():
        converted_source = converter.convert(source_term)
        normalized[converted_source] = target_term
    return normalized


def filter_out_high_risk_terms(
    term_mapping: dict[str, str],
    high_risk_terms: list[str],
    converter,
) -> dict[str, str]:
    protected_terms = set(high_risk_terms)
    protected_terms.update(converter.convert(term) for term in high_risk_terms)

    filtered: dict[str, str] = {}
    for source_term, target_term in term_mapping.items():
        if source_term in protected_terms:
            continue
        if target_term in protected_terms:
            continue
        filtered[source_term] = target_term

    return filtered


def apply_replacements(
    text: str,
    paragraph_index: int,
    term_mapping: dict[str, str],
    file_name: str = "",
) -> tuple[str, list[ReplacementRecord], int]:
    if not term_mapping:
        return text, [], 0

    sorted_terms = sorted(term_mapping.keys(), key=lambda item: len(item), reverse=True)
    pattern = regex.compile("|".join(regex.escape(term) for term in sorted_terms))
    counter: Counter[str] = Counter()

    def _replace(match: regex.Match) -> str:
        source = match.group(0)
        counter[source] += 1
        return term_mapping[source]

    replaced_text = pattern.sub(_replace, text)
    total_replacements = sum(counter.values())
    snippet = text[:80]

    records = [
        ReplacementRecord(
            paragraph_index=paragraph_index,
            original_snippet=snippet,
            replaced_term=source,
            target_term=term_mapping[source],
            replacement_count=count,
            file_name=file_name,
        )
        for source, count in counter.items()
    ]

    return replaced_text, records, total_replacements


# V3.5: validated loader while keeping API compatibility.
def load_term_dict(path: Path) -> dict[str, str]:
    rules = load_low_risk_rules(path)
    return build_low_risk_mapping(rules)
