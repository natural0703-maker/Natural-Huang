from pathlib import Path
from types import SimpleNamespace

from src.gui.worker import GuiRunRequest, ProcessingWorker


def test_worker_success_payload_includes_v3_summary(monkeypatch) -> None:
    fake_result = SimpleNamespace(
        success_count=3,
        failure_count=1,
        total_replacements=9,
        total_review_candidates=4,
        total_anomalies=2,
        report_path=Path("C:/out/report.xlsx"),
        review_summary_path=Path("C:/out/review_summary.xlsx"),
        review_category_counts={"grammar": 2, "wording": 1, "regional_usage": 1},
        top_risk_files=[("a.docx", 3), ("b.docx", 1)],
        low_risk_rules_path=Path("C:/rules/low.yaml"),
        high_risk_rules_path=Path("C:/rules/high.yaml"),
        active_low_risk_rule_count=5,
        active_high_risk_rule_count=16,
        active_config_path=Path("C:/cfg/config.yaml"),
        active_profile="default",
        available_profiles=["default", "strict_tw"],
    )

    def fake_run_processing(options, progress_callback=None):  # noqa: ANN001
        return fake_result

    monkeypatch.setattr("src.gui.worker.run_processing", fake_run_processing)

    worker = ProcessingWorker(
        GuiRunRequest(
            output_dir=Path("C:/out"),
            input_file=Path("C:/in/demo.docx"),
        )
    )

    payloads: list[dict] = []
    worker.success.connect(lambda payload: payloads.append(payload))
    worker.run()

    assert len(payloads) == 1
    payload = payloads[0]
    assert payload["success_count"] == 3
    assert payload["failure_count"] == 1
    assert payload["total_replacements"] == 9
    assert payload["total_review_candidates"] == 4
    assert payload["total_anomalies"] == 2
    assert payload["review_summary_path"].endswith("review_summary.xlsx")
    assert payload["review_category_counts"]["grammar"] == 2
    assert payload["top_risk_files"][0][0] == "a.docx"
    assert payload["low_risk_rules_path"].endswith("low.yaml")
    assert payload["high_risk_rules_path"].endswith("high.yaml")
    assert payload["active_low_risk_rule_count"] == 5
    assert payload["active_high_risk_rule_count"] == 16
    assert payload["active_config_path"].endswith("config.yaml")
    assert payload["active_profile"] == "default"
    assert payload["available_profiles"] == ["default", "strict_tw"]
