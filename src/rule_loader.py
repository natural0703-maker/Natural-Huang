from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


@dataclass(frozen=True)
class LowRiskRule:
    source: str
    target: str
    risk_level: str = "low"
    enabled: bool = True
    category: str = "general"
    note: str = ""


@dataclass(frozen=True)
class HighRiskRule:
    term: str
    risk_category: str
    enabled: bool = True
    suggested_candidates: str = "請人工確認"
    note: str = ""


def _parse_bool(value: Any, default: bool = True) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        text = value.strip().lower()
        if text in {"true", "1", "yes", "y", "on"}:
            return True
        if text in {"false", "0", "no", "n", "off"}:
            return False
    if value is None:
        return default
    return bool(value)


def _load_yaml(path: Path) -> Any:
    if not path.exists():
        raise FileNotFoundError(f"找不到規則檔案：{path}")
    with path.open("r", encoding="utf-8") as fh:
        return yaml.safe_load(fh) or {}


def load_low_risk_rules(path: Path) -> list[LowRiskRule]:
    raw = _load_yaml(path)

    rules: list[LowRiskRule] = []
    if isinstance(raw, dict):
        for source, target in raw.items():
            source_text = str(source).strip()
            target_text = str(target).strip()
            if source_text and target_text:
                rules.append(
                    LowRiskRule(
                        source=source_text,
                        target=target_text,
                        risk_level="low",
                        enabled=True,
                        category="general",
                        note="",
                    )
                )
    elif isinstance(raw, list):
        for idx, item in enumerate(raw, start=1):
            if not isinstance(item, dict):
                raise ValueError(f"低風險詞庫格式錯誤：第 {idx} 筆不是物件。")
            if "source" not in item or "target" not in item:
                raise ValueError(f"低風險詞庫缺少必要欄位：第 {idx} 筆需包含 source 與 target。")

            source_text = str(item.get("source", "")).strip()
            target_text = str(item.get("target", "")).strip()
            if not source_text or not target_text:
                raise ValueError(f"低風險詞庫欄位不可為空白：第 {idx} 筆。")

            rules.append(
                LowRiskRule(
                    source=source_text,
                    target=target_text,
                    risk_level=str(item.get("risk_level", "low")).strip().lower() or "low",
                    enabled=_parse_bool(item.get("enabled", True), default=True),
                    category=str(item.get("category", "general")).strip() or "general",
                    note=str(item.get("note", "")).strip(),
                )
            )
    else:
        raise ValueError("低風險詞庫格式錯誤：僅支援 YAML mapping 或 list。")

    _validate_low_risk_rules(rules)
    return rules


def _validate_low_risk_rules(rules: list[LowRiskRule]) -> None:
    seen_enabled_sources: set[str] = set()
    for item in rules:
        if not item.enabled:
            continue
        if item.source in seen_enabled_sources:
            raise ValueError(f"低風險詞庫有重複啟用規則：source={item.source}")
        if item.source == item.target:
            raise ValueError(f"低風險詞庫規則無效（source 與 target 相同）：{item.source}")
        seen_enabled_sources.add(item.source)


def build_low_risk_mapping(rules: list[LowRiskRule]) -> dict[str, str]:
    mapping: dict[str, str] = {}
    for item in rules:
        if not item.enabled:
            continue
        if item.risk_level == "high":
            continue
        mapping[item.source] = item.target
    return mapping


def load_high_risk_rules(path: Path) -> list[HighRiskRule]:
    raw = _load_yaml(path)
    rules: list[HighRiskRule] = []

    if isinstance(raw, list):
        for idx, item in enumerate(raw, start=1):
            if isinstance(item, str):
                term = item.strip()
                if term:
                    rules.append(
                        HighRiskRule(
                            term=term,
                            risk_category="wording",
                            enabled=True,
                            suggested_candidates="請人工確認",
                            note="",
                        )
                    )
                continue

            if not isinstance(item, dict):
                raise ValueError(f"高風險規則格式錯誤：第 {idx} 筆不是物件。")
            if "term" not in item:
                raise ValueError(f"高風險規則缺少必要欄位：第 {idx} 筆需包含 term。")

            term = str(item.get("term", "")).strip()
            if not term:
                raise ValueError(f"高風險規則 term 不可為空白：第 {idx} 筆。")

            risk_category = str(item.get("risk_category", "wording")).strip() or "wording"
            rules.append(
                HighRiskRule(
                    term=term,
                    risk_category=risk_category,
                    enabled=_parse_bool(item.get("enabled", True), default=True),
                    suggested_candidates=str(item.get("suggested_candidates", "請人工確認")).strip()
                    or "請人工確認",
                    note=str(item.get("note", "")).strip(),
                )
            )
    else:
        raise ValueError("高風險規則格式錯誤：僅支援 YAML list。")

    _validate_high_risk_rules(rules)
    return rules


def _validate_high_risk_rules(rules: list[HighRiskRule]) -> None:
    seen_enabled_terms: set[str] = set()
    for item in rules:
        if not item.enabled:
            continue
        if item.term in seen_enabled_terms:
            raise ValueError(f"高風險規則有重複啟用詞條：term={item.term}")
        if item.risk_category not in {"grammar", "wording", "regional_usage"}:
            raise ValueError(
                f"高風險規則 risk_category 無效：term={item.term}, risk_category={item.risk_category}"
            )
        seen_enabled_terms.add(item.term)


def build_high_risk_term_list(rules: list[HighRiskRule]) -> list[str]:
    return [item.term for item in rules if item.enabled]


def build_high_risk_category_map(rules: list[HighRiskRule]) -> dict[str, str]:
    return {item.term: item.risk_category for item in rules if item.enabled}


def build_high_risk_suggestion_map(rules: list[HighRiskRule]) -> dict[str, str]:
    return {item.term: item.suggested_candidates for item in rules if item.enabled}
