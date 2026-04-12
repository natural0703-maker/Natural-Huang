from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from src.config_loader import AppConfig, load_config
from src.frozen_spec_v1 import HEADING_STYLE_NAME, OPENCC_DEFAULT, PAGE_MARGIN_CM
from src.rule_loader import load_high_risk_rules, load_low_risk_rules

_FLOAT_TOLERANCE = 0.000001


@dataclass(frozen=True)
class Phase1ConfigCheck:
    config: AppConfig
    low_risk_rule_count: int
    high_risk_rule_count: int
    warnings: tuple[str, ...]


def load_phase1_config(config_path: Path | None = None, profile: str | None = None) -> Phase1ConfigCheck:
    config = load_config(config_path, profile_name=profile)
    warnings: list[str] = []

    if config.opencc_config != OPENCC_DEFAULT:
        raise ValueError("OpenCC 預設必須維持 s2t。")
    if config.document_format.heading_style_name != HEADING_STYLE_NAME:
        raise ValueError("章節標題樣式必須維持 Heading 2。")

    margins = (
        config.document_format.page_margin_top_cm,
        config.document_format.page_margin_bottom_cm,
        config.document_format.page_margin_left_cm,
        config.document_format.page_margin_right_cm,
    )
    if any(abs(value - PAGE_MARGIN_CM) > _FLOAT_TOLERANCE for value in margins):
        raise ValueError("頁面邊界必須固定為 1.27 cm。")

    if config.document_format.body_first_line_indent_chars == 2.0:
        warnings.append("body_first_line_indent_chars: 2 為舊設定相容值；Phase 1 格式化實作時需轉為 24 pt。")

    low_risk_rules = load_low_risk_rules(config.default_term_dict_path)
    high_risk_rules = load_high_risk_rules(config.default_high_risk_rules_path)

    return Phase1ConfigCheck(
        config=config,
        low_risk_rule_count=len([rule for rule in low_risk_rules if rule.enabled]),
        high_risk_rule_count=len([rule for rule in high_risk_rules if rule.enabled]),
        warnings=tuple(warnings),
    )
