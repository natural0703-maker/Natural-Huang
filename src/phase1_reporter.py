from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from src.phase1_pipeline import Phase1StubResult
from src.review_schema import ErrorRecord


REPORT_SCHEMA_VERSION = "phase1-report-v1"


@dataclass(frozen=True)
class ReportWriteResult:
    json_report_path: Path | None
    txt_report_path: Path | None
    errors: list[ErrorRecord]


def build_phase1_report_payload(result: Phase1StubResult) -> dict[str, Any]:
    schema = result.schema
    counts = {
        "chapter_candidates": len(schema.chapter_candidates),
        "review_candidates": len(schema.review_candidates),
        "paragraph_merge_candidates": len(schema.paragraph_merge_candidates),
        "errors": len(schema.errors),
    }
    if result.operation == "apply_review":
        apply_result = result.apply_result
        counts.update(
            {
                "applied": apply_result.applied_count if apply_result else 0,
                "skipped": apply_result.skipped_count if apply_result else 0,
                "failed": apply_result.failed_count if apply_result else 0,
            }
        )

    payload: dict[str, Any] = {
        "schema_version": REPORT_SCHEMA_VERSION,
        "operation": result.operation,
        "success": len(schema.errors) == 0,
        "output_path": str(result.output_path) if result.output_path is not None else None,
        "counts": counts,
        "toc": _toc_payload(result),
        "paragraph_merge": _paragraph_merge_payload(result),
        "paragraph_merge_diagnostics": _paragraph_merge_diagnostics_payload(result),
        "config_warnings": _config_warnings(result),
        "errors": [_error_to_dict(error) for error in schema.errors],
    }
    payload[result.operation] = _operation_payload(result)
    return payload


def write_phase1_reports(
    result: Phase1StubResult,
    json_report_path: Path | None,
    txt_report_path: Path | None,
) -> ReportWriteResult:
    if json_report_path is None and txt_report_path is None:
        return ReportWriteResult(json_report_path=None, txt_report_path=None, errors=[])

    payload = build_phase1_report_payload(result)
    errors: list[ErrorRecord] = []
    written_json_path: Path | None = None
    written_txt_path: Path | None = None

    if json_report_path is not None:
        try:
            _ensure_parent(json_report_path)
            json_report_path.write_text(
                json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            written_json_path = json_report_path
        except Exception as exc:
            errors.append(_report_error("REPORT_JSON_WRITE_FAILED", json_report_path, exc))

    if txt_report_path is not None:
        try:
            _ensure_parent(txt_report_path)
            txt_report_path.write_text(_build_txt_report(payload), encoding="utf-8")
            written_txt_path = txt_report_path
        except Exception as exc:
            errors.append(_report_error("REPORT_TXT_WRITE_FAILED", txt_report_path, exc))

    return ReportWriteResult(
        json_report_path=written_json_path,
        txt_report_path=written_txt_path,
        errors=errors,
    )


def _operation_payload(result: Phase1StubResult) -> dict[str, Any]:
    if result.operation == "analyze":
        return {
            "chapter_candidates": len(result.schema.chapter_candidates),
            "review_candidates": len(result.schema.review_candidates),
            "paragraph_merge_candidates": len(result.schema.paragraph_merge_candidates),
        }
    if result.operation == "convert":
        return {
            "converted": result.docx_processed,
            "output_path": str(result.output_path) if result.output_path is not None else None,
            "review_candidates": len(result.schema.review_candidates),
            "paragraph_merge_candidates": len(result.schema.paragraph_merge_candidates),
        }
    if result.operation == "apply_review":
        apply_result = result.apply_result
        candidate_results = getattr(apply_result, "candidate_results", []) if apply_result else []
        return {
            "output_path": str(result.output_path) if result.output_path is not None else None,
            "applied": apply_result.applied_count if apply_result else 0,
            "skipped": apply_result.skipped_count if apply_result else 0,
            "failed": apply_result.failed_count if apply_result else 0,
            "candidate_results": [asdict(candidate_result) for candidate_result in candidate_results],
        }
    return {}


def _build_txt_report(payload: dict[str, Any]) -> str:
    counts = payload["counts"]
    lines = [
        "Phase 1 處理報告",
        f"操作：{payload['operation']}",
        f"成功：{'是' if payload['success'] else '否'}",
        f"輸出檔案：{payload['output_path'] or ''}",
        f"章節候選數：{counts.get('chapter_candidates', 0)}",
        f"高風險候選數：{counts.get('review_candidates', 0)}",
        f"段落合併候選數：{counts.get('paragraph_merge_candidates', 0)}",
        f"錯誤數：{counts.get('errors', 0)}",
        f"TOC 狀態：{payload['toc']['status']}",
        f"TOC fallback：{'是' if payload['toc']['fallback_used'] else '否'}",
        f"TOC 章節數：{payload['toc']['chapter_count']}",
        f"段落合併套用數：{payload['paragraph_merge']['applied_count']}",
        f"段落合併略過數：{payload['paragraph_merge']['skipped_count']}",
        f"段落合併失敗數：{payload['paragraph_merge']['failed_count']}",
        f"段落合併結果碼摘要：{_format_paragraph_merge_codes(payload['paragraph_merge']['codes'])}",
        f"段落合併 mismatch 總數：{payload['paragraph_merge_diagnostics']['total_mismatch_count']}",
        f"段落合併前段 mismatch：{payload['paragraph_merge_diagnostics']['source_mismatch_count']}",
        f"段落合併後段 mismatch：{payload['paragraph_merge_diagnostics']['next_source_mismatch_count']}",
        f"段落合併 mismatch 範例候選：{_format_sample_candidate_ids(payload['paragraph_merge_diagnostics']['sample_candidate_ids'])}",
        f"設定警告數：{len(payload['config_warnings'])}",
    ]
    if payload["operation"] == "apply_review":
        lines.extend(
            [
                f"套用數：{counts.get('applied', 0)}",
                f"略過數：{counts.get('skipped', 0)}",
                f"失敗數：{counts.get('failed', 0)}",
            ]
        )
    if counts.get("errors", 0) > 0 and payload["errors"]:
        first_error = payload["errors"][0]
        lines.append(f"第一個錯誤：{first_error['code']} {first_error['message']}")
    return "\n".join(lines) + "\n"


def _ensure_parent(path: Path) -> None:
    if path.parent and not path.parent.exists():
        path.parent.mkdir(parents=True, exist_ok=True)


def _error_to_dict(error: ErrorRecord) -> dict[str, str]:
    return {
        "code": error.code,
        "message": error.message,
        "technical_detail": error.technical_detail,
    }


def _toc_payload(result: Phase1StubResult) -> dict[str, Any]:
    toc = result.schema.toc
    return {
        "requested": toc.requested,
        "status": toc.status,
        "fallback_used": toc.fallback_used,
        "chapter_count": toc.chapter_count,
    }


def _paragraph_merge_payload(result: Phase1StubResult) -> dict[str, Any]:
    apply_result = result.apply_result
    summary = getattr(apply_result, "paragraph_merge_summary", None) if apply_result is not None else None
    if summary is None:
        return {
            "applied_count": 0,
            "skipped_count": 0,
            "failed_count": 0,
            "codes": {},
        }
    return {
        "applied_count": summary.applied_count,
        "skipped_count": summary.skipped_count,
        "failed_count": summary.failed_count,
        "codes": dict(summary.codes),
    }


def _paragraph_merge_diagnostics_payload(result: Phase1StubResult) -> dict[str, Any]:
    apply_result = result.apply_result
    diagnostics = getattr(apply_result, "paragraph_merge_diagnostics", None) if apply_result is not None else None
    if diagnostics is None:
        return {
            "total_mismatch_count": 0,
            "source_mismatch_count": 0,
            "next_source_mismatch_count": 0,
            "sample_candidate_ids": [],
        }
    return {
        "total_mismatch_count": diagnostics.total_mismatch_count,
        "source_mismatch_count": diagnostics.source_mismatch_count,
        "next_source_mismatch_count": diagnostics.next_source_mismatch_count,
        "sample_candidate_ids": list(diagnostics.sample_candidate_ids),
    }


def _format_paragraph_merge_codes(codes: dict[str, int]) -> str:
    if not codes:
        return "無"
    return ", ".join(f"{code}={count}" for code, count in sorted(codes.items()))


def _format_sample_candidate_ids(candidate_ids: list[str]) -> str:
    if not candidate_ids:
        return "無"
    return ", ".join(candidate_ids[:3])


def _config_warnings(result: Phase1StubResult) -> list[str]:
    config_check = getattr(result, "config_check", None)
    return list(getattr(config_check, "warnings", ())) if config_check is not None else []


def _report_error(code: str, path: Path, exc: Exception) -> ErrorRecord:
    return ErrorRecord(
        code=code,
        message=f"無法寫入報告檔：{path}",
        technical_detail=str(exc),
    )
