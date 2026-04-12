from pathlib import Path
from types import SimpleNamespace

from src.gui.worker import GuiRunRequest, ProcessingWorker


def test_worker_apply_review_payload(monkeypatch) -> None:
    fake_result = SimpleNamespace(
        file_paths=[Path("C:/out/a_TW.docx")],
        output_files=[Path("C:/out/a_TW_reviewed.docx")],
        apply_summary_path=Path("C:/out/apply_summary.xlsx"),
        total_candidates=4,
        applied_count=2,
        skipped_count=1,
        not_found_count=1,
        conflict_count=0,
        failed_count=0,
        failure_count=0,
        reason_counts={"context mismatch": 1},
    )

    def fake_run_apply_review(options, progress_callback=None):  # noqa: ANN001
        return fake_result

    monkeypatch.setattr("src.gui.worker.run_apply_review", fake_run_apply_review)

    worker = ProcessingWorker(
        GuiRunRequest(
            mode="apply_review",
            output_dir=Path("C:/out"),
            apply_review_summary_path=Path("C:/out/review_summary.xlsx"),
            input_file=Path("C:/out/a_TW.docx"),
        )
    )

    payloads: list[dict] = []
    worker.success.connect(lambda payload: payloads.append(payload))
    worker.run()

    assert len(payloads) == 1
    payload = payloads[0]
    assert payload["mode"] == "apply_review"
    assert payload["applied_count"] == 2
    assert payload["total_candidates"] == 4
    assert payload["reviewed_file_path"].endswith("a_TW_reviewed.docx")
