from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from src.processing_service_v3 import (
    ApplyReviewOptions,
    ProcessingOptions,
    run_apply_review,
    run_processing,
)


LOGGER = logging.getLogger("docx_tw_cli")
_PHASE1_FORWARD_FLAGS = frozenset({"--json-report", "--txt-report", "--apply-review"})


def _should_forward_to_phase1(argv: list[str]) -> bool:
    # Keep this forwarding list intentionally conservative. New Phase 1/2
    # features should prefer `python -m src.phase1_cli`; do not expand legacy
    # forwarding just because a new flag exists. In particular,
    # `--reviewed-output` is an output option and must not trigger forwarding
    # by itself.
    return any(arg in _PHASE1_FORWARD_FLAGS for arg in argv)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "DOCX 簡轉繁與人工複核回填工具（V3.6）。"
            "此入口為 legacy compatibility forwarder；新主幹 CLI 建議使用 "
            "`python -m src.phase1_cli`，並僅在既有保守條件下轉發到 src.phase1_cli。"
        )
    )
    input_group = parser.add_mutually_exclusive_group(required=False)
    input_group.add_argument("--input-file", "--input", dest="input_file", help="單一 .docx 輸入路徑")
    input_group.add_argument("--input-dir", help="資料夾輸入路徑（批次模式）")
    parser.add_argument("--recursive", action="store_true", help="遞迴掃描 --input-dir 子資料夾 .docx")
    parser.add_argument("--output-dir", required=True, help="輸出資料夾路徑")
    parser.add_argument("--config", help="設定檔 YAML 路徑")
    parser.add_argument("--profile", help="規則方案名稱（profile）")
    parser.add_argument("--term-dict", help="低風險詞庫 YAML 路徑")
    parser.add_argument("--high-risk-rules", help="高風險規則 YAML 路徑")
    parser.add_argument("--report-name", help="Excel 報告檔名（預設 report.xlsx）")
    parser.add_argument(
        "--apply-review-summary",
        dest="apply_review_summary",
        help="套用人工複核結果（review_summary.xlsx 或 review_summary.csv）",
    )
    return parser


def _setup_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )


def _build_common_paths(args: argparse.Namespace) -> tuple[Path, Path | None, Path | None, Path | None]:
    output_dir = Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    input_file = Path(args.input_file).resolve() if args.input_file else None
    input_dir = Path(args.input_dir).resolve() if args.input_dir else None
    config_path = Path(args.config).resolve() if args.config else None
    return output_dir, input_file, input_dir, config_path


def _validate_input_target(input_file: Path | None, input_dir: Path | None) -> None:
    if input_file is None and input_dir is None:
        raise ValueError("參數錯誤：請提供 `--input-file/--input` 或 `--input-dir` 其中一個。")


def _run_standard_mode(args: argparse.Namespace) -> int:
    output_dir, input_file, input_dir, config_path = _build_common_paths(args)
    _validate_input_target(input_file, input_dir)
    term_dict_path = Path(args.term_dict).resolve() if args.term_dict else None
    high_risk_rules_path = Path(args.high_risk_rules).resolve() if args.high_risk_rules else None

    result = run_processing(
        ProcessingOptions(
            output_dir=output_dir,
            input_file=input_file,
            input_dir=input_dir,
            recursive=bool(args.recursive),
            config_path=config_path,
            term_dict_path=term_dict_path,
            high_risk_rules_path=high_risk_rules_path,
            report_name=args.report_name,
            profile=args.profile,
        )
    )
    for failure in result.batch_result.failures:
        LOGGER.error(
            "File failed: %s | %s | %s",
            failure.file_name,
            failure.error_type,
            failure.error_message,
        )

    print("處理完成。")
    print(f"輸入檔案數：{len(result.file_paths)}")
    print(f"成功：{result.success_count}")
    print(f"失敗：{result.failure_count}")
    print(f"報告檔案：{result.report_path}")
    print(f"待複核報表：{result.review_summary_path}")
    print(f"低風險替換總次數：{result.total_replacements}")
    print(f"高風險候選總數：{result.total_review_candidates}")
    print(f"異常字元總數：{result.total_anomalies}")
    print(f"啟用 profile：{result.active_profile}")
    print(f"低風險詞庫：{result.low_risk_rules_path}")
    print(f"高風險規則：{result.high_risk_rules_path}")
    return 1 if result.failure_count > 0 else 0


def _run_apply_mode(args: argparse.Namespace) -> int:
    output_dir, input_file, input_dir, config_path = _build_common_paths(args)
    _validate_input_target(input_file, input_dir)
    review_summary_path = Path(args.apply_review_summary).resolve()

    result = run_apply_review(
        ApplyReviewOptions(
            output_dir=output_dir,
            apply_review_summary_path=review_summary_path,
            input_file=input_file,
            input_dir=input_dir,
            recursive=bool(args.recursive),
            config_path=config_path,
            profile=args.profile,
        )
    )

    print("人工複核回填完成。")
    print(f"來源檔案數：{len(result.file_paths)}")
    print(f"第二版輸出檔案數：{len(result.output_files)}")
    print(f"總候選數：{result.total_candidates}")
    print(f"實際套用數：{result.applied_count}")
    print(f"跳過數：{result.skipped_count}")
    print(f"找不到定位數：{result.not_found_count}")
    print(f"衝突數：{result.conflict_count}")
    print(f"失敗數：{result.failed_count}")
    if result.reason_counts:
        print("失敗原因分類：")
        for key in sorted(result.reason_counts):
            print(f"- {key}: {result.reason_counts[key]}")
    print(f"套用摘要：{result.apply_summary_path}")
    return 0


def main(argv: list[str] | None = None) -> int:
    _setup_logging()
    raw_argv = list(argv) if argv is not None else sys.argv[1:]
    if _should_forward_to_phase1(raw_argv):
        from src.phase1_cli import main as phase1_main

        return phase1_main(raw_argv)

    args = _build_parser().parse_args(raw_argv)

    try:
        if args.apply_review_summary:
            return _run_apply_mode(args)
        return _run_standard_mode(args)
    except FileNotFoundError as exc:
        print(f"錯誤：{exc}", file=sys.stderr)
        return 1
    except ValueError as exc:
        print(f"錯誤：{exc}", file=sys.stderr)
        return 1
    except Exception:
        LOGGER.exception("執行流程發生未預期錯誤")
        print("錯誤：發生未預期錯誤。", file=sys.stderr)
        return 1
