from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG_PATH = PROJECT_ROOT / "設定檔.yaml"
DEFAULT_HIGH_RISK_RULES_FILENAME = "high_risk_rules.yaml"
LEGACY_HIGH_RISK_RULES_FILENAME = "高風險規則.yaml"


@dataclass(frozen=True)
class DocumentFormatConfig:
    page_margin_top_cm: float = 1.27
    page_margin_bottom_cm: float = 1.27
    page_margin_left_cm: float = 1.27
    page_margin_right_cm: float = 1.27
    body_font_name: str = "\u65b0\u7d30\u660e\u9ad4"
    body_font_size_pt: float = 12.0
    body_space_before_pt: float = 0.0
    body_space_after_pt: float = 6.0
    body_line_spacing_mode: str = "at_least"
    body_min_line_height_pt: float = 12.0
    body_first_line_indent_chars: float = 2.0
    heading_style_name: str = "Heading 2"
    insert_toc: bool = False


@dataclass(frozen=True)
class ProfileConfig:
    name: str
    description: str
    low_risk_dict_path: Path
    high_risk_rules_path: Path
    document_format: DocumentFormatConfig


@dataclass(frozen=True)
class AppConfig:
    opencc_config: str
    default_report_name: str
    default_term_dict_path: Path
    default_high_risk_rules_path: Path
    enable_space_cleanup: bool
    document_format: DocumentFormatConfig
    active_profile: str
    profiles: dict[str, ProfileConfig]


def _load_yaml_file(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh) or {}
    if not isinstance(data, dict):
        raise ValueError(f"invalid config format (mapping required): {path}")
    return data


def _resolve_path(base_dir: Path, raw_path: str | Path) -> Path:
    path = Path(raw_path)
    if path.is_absolute():
        return path
    return (base_dir / path).resolve()


def _default_high_risk_rules_path() -> Path:
    preferred = (PROJECT_ROOT / "data" / DEFAULT_HIGH_RISK_RULES_FILENAME).resolve()
    legacy = (PROJECT_ROOT / "data" / LEGACY_HIGH_RISK_RULES_FILENAME).resolve()
    if not preferred.exists() and legacy.exists():
        return legacy
    return preferred


def _to_float(value: Any, default: float) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _parse_document_format(config_data: dict[str, Any]) -> DocumentFormatConfig:
    raw = config_data.get("document_format", {})
    if not isinstance(raw, dict):
        raw = {}

    return DocumentFormatConfig(
        page_margin_top_cm=_to_float(raw.get("page_margin_top_cm", 1.27), 1.27),
        page_margin_bottom_cm=_to_float(raw.get("page_margin_bottom_cm", 1.27), 1.27),
        page_margin_left_cm=_to_float(raw.get("page_margin_left_cm", 1.27), 1.27),
        page_margin_right_cm=_to_float(raw.get("page_margin_right_cm", 1.27), 1.27),
        body_font_name=str(raw.get("body_font_name", "\u65b0\u7d30\u660e\u9ad4")),
        body_font_size_pt=_to_float(raw.get("body_font_size_pt", 12.0), 12.0),
        body_space_before_pt=_to_float(raw.get("body_space_before_pt", 0.0), 0.0),
        body_space_after_pt=_to_float(raw.get("body_space_after_pt", 6.0), 6.0),
        body_line_spacing_mode=str(raw.get("body_line_spacing_mode", "at_least")).strip().lower(),
        body_min_line_height_pt=_to_float(raw.get("body_min_line_height_pt", 12.0), 12.0),
        body_first_line_indent_chars=_to_float(raw.get("body_first_line_indent_chars", 2.0), 2.0),
        heading_style_name=str(raw.get("heading_style_name", "Heading 2")).strip() or "Heading 2",
        insert_toc=bool(raw.get("insert_toc", False)),
    )


def _parse_document_format_from_raw(raw: dict[str, Any] | None) -> DocumentFormatConfig:
    if not isinstance(raw, dict):
        raw = {}
    return _parse_document_format({"document_format": raw})


def apply_format_overrides(
    base: DocumentFormatConfig,
    overrides: dict[str, Any] | None,
) -> DocumentFormatConfig:
    if not overrides:
        return base

    data = base.__dict__.copy()
    for key, value in overrides.items():
        if key in data:
            data[key] = value

    return DocumentFormatConfig(
        page_margin_top_cm=_to_float(data["page_margin_top_cm"], base.page_margin_top_cm),
        page_margin_bottom_cm=_to_float(data["page_margin_bottom_cm"], base.page_margin_bottom_cm),
        page_margin_left_cm=_to_float(data["page_margin_left_cm"], base.page_margin_left_cm),
        page_margin_right_cm=_to_float(data["page_margin_right_cm"], base.page_margin_right_cm),
        body_font_name=str(data["body_font_name"]),
        body_font_size_pt=_to_float(data["body_font_size_pt"], base.body_font_size_pt),
        body_space_before_pt=_to_float(data["body_space_before_pt"], base.body_space_before_pt),
        body_space_after_pt=_to_float(data["body_space_after_pt"], base.body_space_after_pt),
        body_line_spacing_mode=str(data["body_line_spacing_mode"]).strip().lower(),
        body_min_line_height_pt=_to_float(data["body_min_line_height_pt"], base.body_min_line_height_pt),
        body_first_line_indent_chars=_to_float(
            data["body_first_line_indent_chars"], base.body_first_line_indent_chars
        ),
        heading_style_name=str(data["heading_style_name"]).strip() or base.heading_style_name,
        insert_toc=bool(data["insert_toc"]),
    )


def _parse_profiles(
    config_data: dict[str, Any],
    *,
    base_dir: Path,
    base_term_dict_path: Path,
    base_high_risk_rules_path: Path,
    base_document_format: DocumentFormatConfig,
) -> dict[str, ProfileConfig]:
    profiles_raw = config_data.get("profiles")
    if profiles_raw is None:
        return {
            "default": ProfileConfig(
                name="default",
                description="預設方案（相容舊版設定）",
                low_risk_dict_path=base_term_dict_path,
                high_risk_rules_path=base_high_risk_rules_path,
                document_format=base_document_format,
            )
        }

    parsed: dict[str, ProfileConfig] = {}

    def _build_profile(name: str, payload: dict[str, Any]) -> ProfileConfig:
        low_risk_raw = payload.get("low_risk_dict", str(base_term_dict_path))
        high_risk_raw = payload.get("high_risk_rules", str(base_high_risk_rules_path))
        format_raw = payload.get("format_config", {})
        merged_format = apply_format_overrides(
            base_document_format,
            format_raw if isinstance(format_raw, dict) else {},
        )
        return ProfileConfig(
            name=name,
            description=str(payload.get("description", "")).strip(),
            low_risk_dict_path=_resolve_path(base_dir, str(low_risk_raw)),
            high_risk_rules_path=_resolve_path(base_dir, str(high_risk_raw)),
            document_format=merged_format,
        )

    if isinstance(profiles_raw, dict):
        for key, value in profiles_raw.items():
            profile_name = str(key).strip()
            if not profile_name:
                raise ValueError("設定檔錯誤：profiles 包含空白名稱。")
            if not isinstance(value, dict):
                raise ValueError(f"設定檔錯誤：profile `{profile_name}` 必須是物件。")
            if profile_name in parsed:
                raise ValueError(f"設定檔錯誤：profile 名稱重複：{profile_name}")
            parsed[profile_name] = _build_profile(profile_name, value)
    elif isinstance(profiles_raw, list):
        for idx, item in enumerate(profiles_raw, start=1):
            if not isinstance(item, dict):
                raise ValueError(f"設定檔錯誤：profiles 第 {idx} 筆必須是物件。")
            profile_name = str(item.get("profile_name", "")).strip()
            if not profile_name:
                raise ValueError(f"設定檔錯誤：profiles 第 {idx} 筆缺少 profile_name。")
            if profile_name in parsed:
                raise ValueError(f"設定檔錯誤：profile 名稱重複：{profile_name}")
            parsed[profile_name] = _build_profile(profile_name, item)
    else:
        raise ValueError("設定檔錯誤：profiles 只能是 mapping 或 list。")

    if not parsed:
        raise ValueError("設定檔錯誤：profiles 不可為空。")
    return parsed


def _validate_profile_files(profiles: dict[str, ProfileConfig]) -> None:
    from src.rule_loader import load_high_risk_rules, load_low_risk_rules

    for name, profile in profiles.items():
        if not profile.low_risk_dict_path.exists():
            raise FileNotFoundError(
                f"找不到 profile `{name}` 的低風險詞庫檔案：{profile.low_risk_dict_path}"
            )
        if not profile.high_risk_rules_path.exists():
            raise FileNotFoundError(
                f"找不到 profile `{name}` 的高風險規則檔案：{profile.high_risk_rules_path}"
            )
        try:
            load_low_risk_rules(profile.low_risk_dict_path)
        except Exception as exc:
            raise ValueError(
                f"profile `{name}` 的低風險詞庫格式錯誤：{exc}"
            ) from exc
        try:
            load_high_risk_rules(profile.high_risk_rules_path)
        except Exception as exc:
            raise ValueError(
                f"profile `{name}` 的高風險規則格式錯誤：{exc}"
            ) from exc


def load_config(config_path: Path | None, profile_name: str | None = None) -> AppConfig:
    if config_path is None:
        source_path = DEFAULT_CONFIG_PATH
    else:
        source_path = config_path.resolve()

    if not source_path.exists():
        raise FileNotFoundError(f"missing config file: {source_path}")

    config_data = _load_yaml_file(source_path)
    base_dir = source_path.parent

    opencc_config = str(config_data.get("opencc_config", "s2t"))
    default_report_name = str(config_data.get("default_report_name", "report.xlsx"))
    if "default_term_dict_path" in config_data:
        term_dict_raw = config_data.get("default_term_dict_path")
        base_term_dict_path = _resolve_path(base_dir, str(term_dict_raw))
    else:
        base_term_dict_path = (PROJECT_ROOT / "data" / "低風險詞庫.yaml").resolve()

    if "default_high_risk_rules_path" in config_data:
        high_risk_rules_raw = config_data.get("default_high_risk_rules_path")
        base_high_risk_rules_path = _resolve_path(base_dir, str(high_risk_rules_raw))
    else:
        base_high_risk_rules_path = _default_high_risk_rules_path()

    enable_space_cleanup = bool(config_data.get("enable_space_cleanup", True))
    base_document_format = _parse_document_format(config_data)

    profiles = _parse_profiles(
        config_data,
        base_dir=base_dir,
        base_term_dict_path=base_term_dict_path,
        base_high_risk_rules_path=base_high_risk_rules_path,
        base_document_format=base_document_format,
    )
    _validate_profile_files(profiles)

    configured_active = str(config_data.get("active_profile", "")).strip() or "default"
    active_profile = profile_name.strip() if profile_name else configured_active
    if active_profile not in profiles:
        available = ", ".join(sorted(profiles.keys()))
        raise ValueError(
            f"找不到 profile：`{active_profile}`。可用 profile：{available}"
        )
    selected_profile = profiles[active_profile]

    return AppConfig(
        opencc_config=opencc_config,
        default_report_name=default_report_name,
        default_term_dict_path=selected_profile.low_risk_dict_path,
        default_high_risk_rules_path=selected_profile.high_risk_rules_path,
        enable_space_cleanup=enable_space_cleanup,
        document_format=selected_profile.document_format,
        active_profile=active_profile,
        profiles=profiles,
    )
