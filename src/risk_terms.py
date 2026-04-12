from __future__ import annotations


from pathlib import Path

from src.rule_loader import HighRiskRule


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_HIGH_RISK_RULES_FILENAME = "high_risk_rules.yaml"
LEGACY_HIGH_RISK_RULES_FILENAME = "高風險規則.yaml"


def _default_high_risk_rules_path() -> Path:
    preferred = PROJECT_ROOT / "data" / DEFAULT_HIGH_RISK_RULES_FILENAME
    legacy = PROJECT_ROOT / "data" / LEGACY_HIGH_RISK_RULES_FILENAME
    if not preferred.exists() and legacy.exists():
        return legacy
    return preferred


DEFAULT_HIGH_RISK_RULES_PATH = _default_high_risk_rules_path()


HIGH_RISK_TERMS: list[str] = [
    "得",
    "的",
    "地",
    "裡",
    "裏",
    "於",
    "在",
    "質量",
    "優化",
    "信息",
    "訊息",
    "資訊",
    "視頻",
    "影片",
    "視訊",
    "支持",
]

DEFAULT_HIGH_RISK_RULES: list[HighRiskRule] = [
    HighRiskRule(term="得", risk_category="grammar", suggested_candidates="請依語境確認「的/得/地」"),
    HighRiskRule(term="的", risk_category="grammar", suggested_candidates="請依語境確認「的/得/地」"),
    HighRiskRule(term="地", risk_category="grammar", suggested_candidates="請依語境確認「的/得/地」"),
    HighRiskRule(term="裡", risk_category="regional_usage", suggested_candidates="請依語境確認「裡/裏」"),
    HighRiskRule(term="裏", risk_category="regional_usage", suggested_candidates="請依語境確認「裡/裏」"),
    HighRiskRule(term="於", risk_category="regional_usage", suggested_candidates="請依語境確認「於/在」"),
    HighRiskRule(term="在", risk_category="regional_usage", suggested_candidates="請依語境確認「於/在」"),
    HighRiskRule(term="質量", risk_category="wording", suggested_candidates="建議確認是否改為「品質」"),
    HighRiskRule(term="優化", risk_category="wording", suggested_candidates="建議確認是否改為「最佳化/優化」"),
    HighRiskRule(term="信息", risk_category="wording", suggested_candidates="建議確認是否改為「資訊/訊息」"),
    HighRiskRule(term="訊息", risk_category="wording", suggested_candidates="建議確認是否改為「資訊/訊息」"),
    HighRiskRule(term="資訊", risk_category="wording", suggested_candidates="建議確認是否改為「資訊/訊息」"),
    HighRiskRule(term="視頻", risk_category="wording", suggested_candidates="建議確認是否改為「影片/視訊」"),
    HighRiskRule(term="影片", risk_category="wording", suggested_candidates="建議確認是否改為「影片/視訊」"),
    HighRiskRule(term="視訊", risk_category="wording", suggested_candidates="建議確認是否改為「影片/視訊」"),
    HighRiskRule(term="支持", risk_category="wording", suggested_candidates="建議確認是否改為「支援/支持」"),
]
