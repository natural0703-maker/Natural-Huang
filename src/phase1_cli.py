from __future__ import annotations

import argparse
import sys
from pathlib import Path

from src.phase1_pipeline import Phase1Options, Phase1StubResult, analyze, apply_review, convert
from src.phase1_reporter import write_phase1_reports


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="DOCX 小說簡轉繁工具 Phase 1 CLI")
    parser.add_argument("--input")
    parser.add_argument("--output-dir")
    parser.add_argument("--config")
    parser.add_argument("--profile")
    parser.add_argument("--create-toc", dest="create_toc", action="store_true", default=True)
    parser.add_argument("--no-create-toc", dest="create_toc", action="store_false")
    parser.add_argument("--chapter-page-break", dest="chapter_page_break", action="store_true", default=False)
    parser.add_argument("--no-chapter-page-break", dest="chapter_page_break", action="store_false")
    parser.add_argument("--chapter-review")
    parser.add_argument("--json-report")
    parser.add_argument("--txt-report")
    parser.add_argument("--apply-review")
    parser.add_argument("--reviewed-output")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    options = Phase1Options(
        input_path=_to_path(args.input),
        output_dir=_to_path(args.output_dir),
        config_path=_to_path(args.config),
        profile=args.profile,
        create_toc=bool(args.create_toc),
        chapter_page_break=bool(args.chapter_page_break),
        chapter_review_path=_to_path(args.chapter_review),
        json_report_path=_to_path(args.json_report),
        txt_report_path=_to_path(args.txt_report),
        apply_review_path=_to_path(args.apply_review),
        reviewed_output_path=_to_path(args.reviewed_output),
    )

    try:
        result = _dispatch(options)
    except Exception:
        print("錯誤：發生未預期錯誤。", file=sys.stderr)
        return 1

    report_result = write_phase1_reports(result, options.json_report_path, options.txt_report_path)
    _print_stdout_summary(result)
    if result.schema.errors:
        for error in result.schema.errors:
            print(f"錯誤：{error.code} {error.message}", file=sys.stderr)
    if report_result.errors:
        for error in report_result.errors:
            print(f"錯誤：{error.code} {error.message}", file=sys.stderr)
    if result.schema.errors or report_result.errors:
        return 1
    return 0


def _dispatch(options: Phase1Options) -> Phase1StubResult:
    if options.apply_review_path is not None:
        return apply_review(options)
    if options.output_dir is not None:
        return convert(options)
    return analyze(options)


def _print_stdout_summary(result: Phase1StubResult) -> None:
    print(f"模式：{result.operation}")
    if result.operation == "analyze":
        print(f"章節候選數：{len(result.schema.chapter_candidates)}")
        print(f"高風險候選數：{len(result.schema.review_candidates)}")
        print(f"段落合併候選數：{len(result.schema.paragraph_merge_candidates)}")
        return
    if result.operation == "convert":
        print(f"輸出檔：{result.output_path or ''}")
        print(f"高風險候選數：{len(result.schema.review_candidates)}")
        print(f"錯誤數：{len(result.schema.errors)}")
        return
    if result.operation == "apply_review":
        apply_result = result.apply_result
        print(f"輸出檔：{result.output_path or ''}")
        print(f"套用數：{apply_result.applied_count if apply_result else 0}")
        print(f"略過數：{apply_result.skipped_count if apply_result else 0}")
        print(f"失敗數：{apply_result.failed_count if apply_result else 0}")


def _to_path(value: str | None) -> Path | None:
    return Path(value) if value else None


if __name__ == "__main__":
    raise SystemExit(main())
