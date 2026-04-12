import src.config_loader as config_loader
from src.config_loader import load_config
from tests.test_paths import make_test_dir


def test_opencc_default_is_s2t_when_not_specified() -> None:
    tmp_path = make_test_dir("config_defaults")
    config_path = tmp_path / "config.yaml"
    term_dict_path = tmp_path / "term_dict.yaml"
    term_dict_path.write_text('"x": "y"\n', encoding="utf-8")
    config_path.write_text(
        "default_report_name: report.xlsx\n"
        "default_term_dict_path: term_dict.yaml\n"
        "enable_space_cleanup: true\n",
        encoding="utf-8",
    )

    config = load_config(config_path)
    assert config.opencc_config == "s2t"
    assert config.document_format.body_font_size_pt == 12.0
    assert config.document_format.body_first_line_indent_chars == 2.0
    assert config.default_high_risk_rules_path.name == "high_risk_rules.yaml"


def test_default_high_risk_rules_falls_back_to_legacy_chinese_name(monkeypatch) -> None:
    tmp_path = make_test_dir("config_defaults_legacy_high")
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    config_path = tmp_path / "config.yaml"
    term_dict_path = tmp_path / "term_dict.yaml"
    legacy_high_path = data_dir / "高風險規則.yaml"
    term_dict_path.write_text('"x": "y"\n', encoding="utf-8")
    legacy_high_path.write_text("- term: 得\n  risk_category: grammar\n", encoding="utf-8")
    config_path.write_text(
        "default_report_name: report.xlsx\n"
        "default_term_dict_path: term_dict.yaml\n"
        "enable_space_cleanup: true\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(config_loader, "PROJECT_ROOT", tmp_path)

    config = load_config(config_path)

    assert config.default_high_risk_rules_path == legacy_high_path.resolve()


def test_explicit_high_risk_rules_path_is_not_rewritten(monkeypatch) -> None:
    tmp_path = make_test_dir("config_defaults_explicit_high")
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    config_path = tmp_path / "config.yaml"
    term_dict_path = tmp_path / "term_dict.yaml"
    explicit_high_path = tmp_path / "custom_high.yaml"
    term_dict_path.write_text('"x": "y"\n', encoding="utf-8")
    (data_dir / "high_risk_rules.yaml").write_text("- term: 得\n  risk_category: grammar\n", encoding="utf-8")
    explicit_high_path.write_text("- term: 的\n  risk_category: grammar\n", encoding="utf-8")
    config_path.write_text(
        "default_report_name: report.xlsx\n"
        "default_term_dict_path: term_dict.yaml\n"
        "default_high_risk_rules_path: custom_high.yaml\n"
        "enable_space_cleanup: true\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(config_loader, "PROJECT_ROOT", tmp_path)

    config = load_config(config_path)

    assert config.default_high_risk_rules_path == explicit_high_path.resolve()
