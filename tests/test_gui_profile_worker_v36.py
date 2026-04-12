from pathlib import Path
from types import SimpleNamespace

from src.gui.worker import GuiRunRequest, ProcessingWorker


def test_worker_passes_profile_to_processing_options(monkeypatch) -> None:
    captured: dict[str, str] = {}

    def fake_run_processing(options, progress_callback=None):  # noqa: ANN001
        captured["profile"] = options.profile
        return SimpleNamespace(
            success_count=1,
            failure_count=0,
            total_replacements=0,
            total_review_candidates=0,
            total_anomalies=0,
            report_path=Path("C:/out/report.xlsx"),
            review_summary_path=Path("C:/out/review_summary.xlsx"),
            review_category_counts={"grammar": 0, "wording": 0, "regional_usage": 0},
            top_risk_files=[],
            low_risk_rules_path=Path("C:/rules/low.yaml"),
            high_risk_rules_path=Path("C:/rules/high.yaml"),
            active_low_risk_rule_count=1,
            active_high_risk_rule_count=1,
            active_config_path=Path("C:/cfg/config.yaml"),
            active_profile="strict_tw",
            available_profiles=["default", "strict_tw"],
        )

    monkeypatch.setattr("src.gui.worker.run_processing", fake_run_processing)

    worker = ProcessingWorker(
        GuiRunRequest(
            output_dir=Path("C:/out"),
            input_file=Path("C:/in/demo.docx"),
            profile="strict_tw",
        )
    )
    payloads: list[dict] = []
    worker.success.connect(lambda payload: payloads.append(payload))
    worker.run()

    assert captured["profile"] == "strict_tw"
    assert payloads[0]["active_profile"] == "strict_tw"
