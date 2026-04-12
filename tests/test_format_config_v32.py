from src.config_loader import DocumentFormatConfig, load_config
from src.docx_writer import ParagraphOutput, write_paragraphs_to_docx
from tests.test_paths import make_test_dir
from docx import Document


def test_document_format_defaults_when_missing() -> None:
    tmp = make_test_dir("format_defaults_v32")
    config_path = tmp / "config.yaml"
    term_dict_path = tmp / "term_dict.yaml"
    term_dict_path.write_text('"x": "y"\n', encoding="utf-8")
    config_path.write_text(
        "opencc_config: s2t\n"
        "default_report_name: report.xlsx\n"
        "default_term_dict_path: term_dict.yaml\n"
        "enable_space_cleanup: true\n",
        encoding="utf-8",
    )

    config = load_config(config_path)
    assert config.document_format == DocumentFormatConfig()


def test_document_format_override_from_config() -> None:
    tmp = make_test_dir("format_override_v32")
    config_path = tmp / "config.yaml"
    term_dict_path = tmp / "term_dict.yaml"
    term_dict_path.write_text('"x": "y"\n', encoding="utf-8")
    config_path.write_text(
        "opencc_config: s2t\n"
        "default_report_name: report.xlsx\n"
        "default_term_dict_path: term_dict.yaml\n"
        "enable_space_cleanup: true\n"
        "document_format:\n"
        "  body_font_name: PMingLiU\n"
        "  body_font_size_pt: 14\n"
        "  body_first_line_indent_chars: 3\n"
        "  body_space_after_pt: 8\n"
        "  page_margin_top_cm: 2.0\n"
        "  heading_style_name: Heading 2\n",
        encoding="utf-8",
    )

    config = load_config(config_path)
    assert config.document_format.body_font_name == "PMingLiU"
    assert config.document_format.body_font_size_pt == 14.0
    assert config.document_format.body_first_line_indent_chars == 3.0
    assert config.document_format.body_space_after_pt == 8.0
    assert config.document_format.page_margin_top_cm == 2.0


def test_document_format_override_applies_to_output_docx() -> None:
    tmp = make_test_dir("format_apply_v32")
    out_path = tmp / "out.docx"
    fmt = DocumentFormatConfig(
        page_margin_top_cm=2.0,
        page_margin_bottom_cm=2.0,
        page_margin_left_cm=2.0,
        page_margin_right_cm=2.0,
        body_font_name="PMingLiU",
        body_font_size_pt=14.0,
        body_space_after_pt=8.0,
        body_first_line_indent_chars=3.0,
        heading_style_name="Heading 2",
    )

    write_paragraphs_to_docx(
        [
            ParagraphOutput("\u7b2c\u4e00\u7ae0", is_heading=True),
            ParagraphOutput("\u6e2c\u8a66\u5167\u6587", is_heading=False),
        ],
        out_path,
        document_format=fmt,
    )

    doc = Document(str(out_path))
    section = doc.sections[0]
    assert abs(section.top_margin.cm - 2.0) < 0.01

    body = doc.paragraphs[1]
    assert body.runs[0].font.size is not None
    assert abs(body.runs[0].font.size.pt - 14.0) < 0.01
    assert body.paragraph_format.first_line_indent is not None
    assert abs(body.paragraph_format.first_line_indent.pt - 42.0) < 0.01
