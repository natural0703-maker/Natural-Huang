from pathlib import Path

from docx import Document

from src.processing_service_v3 import ProcessingOptions, run_processing
from tests.test_paths import make_test_dir


def _make_docx(path: Path, paragraphs: list[str]) -> None:
    doc = Document()
    for text in paragraphs:
        doc.add_paragraph(text)
    doc.save(str(path))


def test_processing_result_includes_review_summary_and_category_counts() -> None:
    tmp = make_test_dir("processing_v33")
    input_file = tmp / "novel.docx"
    output_dir = tmp / "out"
    output_dir.mkdir(parents=True, exist_ok=True)

    _make_docx(
        input_file,
        [
            "第一章 測試",
            "這裡的資訊支持人工複核。",
            "他的影片資訊需要確認。",
        ],
    )

    result = run_processing(
        ProcessingOptions(
            input_file=input_file,
            output_dir=output_dir,
        )
    )

    assert result.report_path.exists()
    assert result.review_summary_path.exists()
    assert result.total_review_candidates > 0
    assert result.review_category_counts["grammar"] >= 1
    assert result.review_category_counts["wording"] >= 1
    assert isinstance(result.top_risk_files, list)
    assert result.top_risk_files
