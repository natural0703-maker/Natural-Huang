from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from src.batch_runner import collect_input_files, process_single_file, run_batch
from src.config_loader import load_config
from src.converter import OpenCCConverter
from src.replacer import (
    filter_out_high_risk_terms,
    load_term_dict,
    normalize_terms_with_converter,
)
from src.report_writer import write_report
from src.risk_terms import HIGH_RISK_TERMS


LOGGER = logging.getLogger("docx_tw_cli")


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="DOCX 簡轉繁處理工具（V3.0）")
    input_group = parser.add_mutually_exclusive_group(required=False)
    input_group.add_argument(
        "--input-file",
        "--input",
        dest="input_file",
        help="單一 .docx 輸入路徑",
    )
    input_group.add_argument("--input-dir", help="資料夾輸入路徑（批次模式）")
    parser.add_argument(
        "--recursive",
        action="store_true",
        help="遞迴掃描 --input-dir 子資料夾中的 .docx",
    )
    parser.add_argument("--output-dir", required=True, help="輸出資料夾路徑")
    parser.add_argument("--config", help="設定檔 YAML 路徑")
    parser.add_argument("--term-dict", help="低風險詞庫 YAML 路徑")
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


def main(argv: list[str] | None = None) -> int:
    _setup_logging()
    args = _build_parser().parse_args(argv)

    try:
        output_dir = Path(args.output_dir).resolve()
        input_file = Path(args.input_file).resolve() if args.input_file else None
        input_dir = Path(args.input_dir).resolve() if args.input_dir else None
        config_path = Path(args.config).resolve() if args.config else None
        term_dict_arg = Path(args.term_dict).resolve() if args.term_dict else None

        output_dir.mkdir(parents=True, exist_ok=True)

        config = load_config(config_path)
        report_name = args.report_name if args.report_name else config.default_report_name
        term_dict_path = term_dict_arg if term_dict_arg else config.default_term_dict_path

        file_paths = collect_input_files(
            input_file=input_file,
            input_dir=input_dir,
            recursive=bool(args.recursive),
        )
        if not file_paths:
            print("錯誤：找不到可處理的 .docx 檔案。", file=sys.stderr)
            return 1

        converter = OpenCCConverter(config.opencc_config)
        raw_term_mapping = load_term_dict(term_dict_path)
        term_mapping = normalize_terms_with_converter(raw_term_mapping, converter)
        term_mapping = filter_out_high_risk_terms(
            term_mapping=term_mapping,
            high_risk_terms=HIGH_RISK_TERMS,
            converter=converter,
        )

        def _processor(file_path: Path):
            return process_single_file(
                file_path=file_path,
                output_dir=output_dir,
                converter=converter,
                term_mapping=term_mapping,
                enable_space_cleanup=config.enable_space_cleanup,
                document_format=config.document_format,
            )

        batch_result = run_batch(file_paths=file_paths, processor=_processor)
        report_path = output_dir / report_name
        write_report(
            report_path=report_path,
            summaries=batch_result.summaries,
            replacement_records=batch_result.replacements,
            review_candidates=batch_result.review_candidates,
            anomalies=batch_result.anomalies,
            failures=batch_result.failures,
        )

        success_count = sum(1 for item in batch_result.summaries if item.status == "success")
        failure_count = len(batch_result.failures)
        total_replacements = sum(item.total_replacements for item in batch_result.summaries)

        for failure in batch_result.failures:
            LOGGER.error(
                "File failed: %s | %s | %s",
                failure.file_name,
                failure.error_type,
                failure.error_message,
            )

        print("處理完成。")
        print(f"輸入檔案數：{len(file_paths)}")
        print(f"成功：{success_count}")
        print(f"失敗：{failure_count}")
        print(f"報告檔案：{report_path}")
        print(f"低風險替換總次數：{total_replacements}")
        return 1 if failure_count > 0 else 0
    except FileNotFoundError as exc:
        print(f"錯誤：{exc}", file=sys.stderr)
        return 1
    except ValueError as exc:
        print(f"錯誤：{exc}", file=sys.stderr)
        return 1
    except Exception:
        LOGGER.exception("未預期錯誤")
        print("錯誤：發生未預期錯誤。", file=sys.stderr)
        return 1
