import src.cli_v35 as cli_v35
import src.phase1_cli as phase1_cli
import pytest


def test_should_forward_to_phase1_for_report_and_apply_flags() -> None:
    assert cli_v35._should_forward_to_phase1(["--json-report", "report.json"])
    assert cli_v35._should_forward_to_phase1(["--txt-report", "report.txt"])
    assert cli_v35._should_forward_to_phase1(["--apply-review", "review.json"])


def test_should_not_forward_to_phase1_for_reviewed_output_alone() -> None:
    assert not cli_v35._should_forward_to_phase1(["--reviewed-output", "reviewed.docx"])


def test_should_not_forward_to_phase1_for_deferred_phase1_flags() -> None:
    assert not cli_v35._should_forward_to_phase1(["--chapter-review", "chapter.json"])
    assert not cli_v35._should_forward_to_phase1(["--create-toc"])
    assert not cli_v35._should_forward_to_phase1(["--no-create-toc"])
    assert not cli_v35._should_forward_to_phase1(["--chapter-page-break"])
    assert not cli_v35._should_forward_to_phase1(["--no-chapter-page-break"])


def test_should_not_forward_to_phase1_for_legacy_cli_flags() -> None:
    assert not cli_v35._should_forward_to_phase1(
        [
            "--input-file",
            "input.docx",
            "--output-dir",
            "out",
            "--config",
            "config.yaml",
            "--profile",
            "default",
        ]
    )
    assert not cli_v35._should_forward_to_phase1(["--apply-review-summary", "review_summary.xlsx"])


def test_help_mentions_legacy_forwarder_and_phase1_cli(capsys) -> None:
    parser = cli_v35._build_parser()

    with pytest.raises(SystemExit) as exc_info:
        parser.parse_args(["--help"])

    assert exc_info.value.code == 0
    captured = capsys.readouterr()
    assert "legacy compatibility forwarder" in captured.out
    assert "python -m src.phase1_cli" in captured.out


def test_main_forwards_phase1_argv_and_exit_code(monkeypatch) -> None:
    received: list[list[str]] = []

    def fake_phase1_main(argv):
        received.append(argv)
        return 7

    monkeypatch.setattr(phase1_cli, "main", fake_phase1_main)
    argv = ["--apply-review", "review.json", "--reviewed-output", "reviewed.docx"]

    assert cli_v35.main(argv) == 7
    assert received == [argv]
