from docx import Document

from src.cli_v3 import main
from tests.test_paths import make_test_dir


def test_cli_still_works_with_default_options() -> None:
    tmp = make_test_dir("cli_compat_v32")
    input_docx = tmp / "input.docx"
    output_dir = tmp / "out"
    output_dir.mkdir(parents=True, exist_ok=True)
    term_dict = tmp / "term_dict.yaml"
    config = tmp / "config.yaml"

    doc = Document()
    doc.add_paragraph("软件 文档")
    doc.save(str(input_docx))

    term_dict.write_text('"软件": "軟體"\n"文档": "文件"\n', encoding="utf-8")
    config.write_text(
        "opencc_config: s2t\n"
        "default_report_name: report.xlsx\n"
        "default_term_dict_path: term_dict.yaml\n"
        "enable_space_cleanup: true\n",
        encoding="utf-8",
    )

    exit_code = main(
        [
            "--input-file",
            str(input_docx),
            "--output-dir",
            str(output_dir),
            "--config",
            str(config),
        ]
    )
    assert exit_code == 0
