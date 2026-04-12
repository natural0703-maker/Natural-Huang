from pathlib import Path

from docx import Document

from src.batch_runner import FileProcessResult, collect_input_files, run_batch
from src.batch_runner import process_single_file
from src.models import SummaryRecord
from tests.test_paths import make_test_dir


def test_batch_runner_continue_on_failure() -> None:
    tmp_path = make_test_dir("batch_continue")
    file_a = tmp_path / "a.docx"
    file_b = tmp_path / "b.docx"
    file_a.touch()
    file_b.touch()

    def fake_processor(path: Path) -> FileProcessResult:
        if path.name == "a.docx":
            return FileProcessResult(
                summary=SummaryRecord(
                    file_name=path.name,
                    status="success",
                    paragraph_count=1,
                    total_replacements=1,
                    total_review_candidates=1,
                    total_anomalies=0,
                    elapsed_time_sec=0.01,
                    output_file="C:/out/a_TW.docx",
                ),
                replacements=[],
                review_candidates=[],
                anomalies=[],
            )
        raise RuntimeError("simulated failure")

    result = run_batch([file_a, file_b], processor=fake_processor)
    assert len(result.summaries) == 2
    assert len(result.failures) == 1
    assert result.failures[0].file_name == "b.docx"


def test_collect_input_files_ignores_non_docx_in_directory() -> None:
    tmp_path = make_test_dir("batch_collect")
    (tmp_path / "a.docx").touch()
    (tmp_path / "b.txt").touch()
    (tmp_path / "c.doc").touch()

    files = collect_input_files(
        input_file=None,
        input_dir=tmp_path,
        recursive=False,
    )

    assert len(files) == 1
    assert files[0].name == "a.docx"


def test_real_bad_docx_is_recorded_in_failures() -> None:
    tmp_path = make_test_dir("batch_bad_docx")
    out_dir = tmp_path / "out"
    out_dir.mkdir()

    good_docx = tmp_path / "ok.docx"
    bad_docx = tmp_path / "bad.docx"

    doc = Document()
    doc.add_paragraph("測試段落")
    doc.save(str(good_docx))

    bad_docx.write_text("not a real docx package", encoding="utf-8")

    class DummyConverter:
        def convert(self, text: str) -> str:
            return text

    def processor(path: Path) -> FileProcessResult:
        return process_single_file(
            file_path=path,
            output_dir=out_dir,
            converter=DummyConverter(),
            term_mapping={},
            enable_space_cleanup=True,
        )

    result = run_batch([good_docx, bad_docx], processor=processor)
    assert len(result.failures) == 1
    assert result.failures[0].file_name == "bad.docx"
