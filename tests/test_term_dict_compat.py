from src.replacer import load_term_dict
from tests.test_paths import make_test_dir


def test_term_dict_supports_old_mapping_format() -> None:
    tmp = make_test_dir("term_dict_mapping")
    path = tmp / "term.yaml"
    path.write_text('"软件": "軟體"\n', encoding="utf-8")

    mapping = load_term_dict(path)
    assert mapping == {"软件": "軟體"}


def test_term_dict_supports_extended_list_format() -> None:
    tmp = make_test_dir("term_dict_list")
    path = tmp / "term.yaml"
    path.write_text(
        "- source: 软件\n"
        "  target: 軟體\n"
        "  risk_level: low\n"
        "  enabled: true\n"
        "  note: keep\n"
        "- source: 支持\n"
        "  target: 支援\n"
        "  risk_level: high\n"
        "  enabled: true\n"
        "- source: 文档\n"
        "  target: 文件\n"
        "  enabled: false\n",
        encoding="utf-8",
    )

    mapping = load_term_dict(path)
    assert mapping == {"软件": "軟體"}
