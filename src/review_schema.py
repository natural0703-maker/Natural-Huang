from __future__ import annotations

from dataclasses import dataclass, field
from hashlib import sha256
from typing import Any, Literal

from src.frozen_spec_v1 import STATUS_AUTO_ACCEPTED, STATUS_VALUES


Status = Literal["pending", "accepted", "rejected", "skip", "auto_accepted"]
SUPPORTED_REVIEW_CANDIDATE_TYPES = {"high_risk_term"}


def _hash12(parts: list[object]) -> str:
    text = "\n".join(str(part) for part in parts)
    return sha256(text.encode("utf-8")).hexdigest()[:12]


def make_chapter_candidate_id(paragraph_index: int, matched_rule_id: str, source_text: str) -> str:
    digest = _hash12(["chapter", paragraph_index, matched_rule_id, source_text])
    return f"chapter:{paragraph_index}:{matched_rule_id}:{digest}"


def make_review_candidate_id(rule_id: str, paragraph_index: int, char_start: int, source_text: str) -> str:
    digest = _hash12(["high_risk_term", rule_id, paragraph_index, char_start, source_text])
    return f"risk:{rule_id}:{paragraph_index}:{char_start}:{digest}"


def make_paragraph_merge_candidate_id(paragraph_index: int, next_paragraph_index: int, source_text: str) -> str:
    digest = _hash12(["paragraph_merge", paragraph_index, next_paragraph_index, source_text])
    return f"paragraph_merge:{paragraph_index}:{next_paragraph_index}:{digest}"


@dataclass(frozen=True)
class ChapterCandidate:
    candidate_id: str
    type: str = "chapter"
    status: Status = "pending"
    source_text: str = ""
    resolved_text: str = ""
    normalized_title: str = ""
    paragraph_index: int = -1
    matched_rule_id: str = ""
    confidence: float = 0.0
    auto_accept: bool = False


@dataclass(frozen=True)
class ReviewCandidate:
    candidate_id: str
    type: str = "high_risk_term"
    status: Status = "pending"
    source_text: str = ""
    resolved_text: str = ""
    rule_id: str = ""
    paragraph_index: int = -1
    char_start: int = -1
    char_end: int = -1
    context_before: str = ""
    context_after: str = ""
    risk_category: str = ""


@dataclass(frozen=True)
class ParagraphMergeCandidate:
    candidate_id: str
    type: str = "paragraph_merge"
    status: Status = "pending"
    paragraph_index: int = -1
    next_paragraph_index: int = -1
    source_text: str = ""
    next_text: str = ""
    auto_apply: bool = False
    reason: str = ""


@dataclass(frozen=True)
class TocState:
    requested: bool = False
    status: str = "not_requested"
    fallback_used: bool = False
    chapter_count: int = 0


@dataclass(frozen=True)
class WarningRecord:
    code: str
    message: str
    detail: str = ""


@dataclass(frozen=True)
class ErrorRecord:
    code: str
    message: str
    technical_detail: str = ""


@dataclass(frozen=True)
class ReviewSchema:
    chapter_candidates: list[ChapterCandidate] = field(default_factory=list)
    review_candidates: list[ReviewCandidate] = field(default_factory=list)
    paragraph_merge_candidates: list[ParagraphMergeCandidate] = field(default_factory=list)
    toc: TocState = field(default_factory=TocState)
    warnings: list[WarningRecord] = field(default_factory=list)
    errors: list[ErrorRecord] = field(default_factory=list)


def validate_review_schema(schema: ReviewSchema) -> None:
    for candidate in schema.chapter_candidates:
        _validate_status(candidate.status)
        if candidate.type != "chapter":
            raise ValueError("chapter_candidates 的 type 必須是 chapter。")
    for candidate in schema.review_candidates:
        _validate_status(candidate.status)
        if candidate.status == STATUS_AUTO_ACCEPTED:
            raise ValueError("review_candidates 不允許 auto_accepted。")
        if candidate.type != "high_risk_term":
            raise ValueError("review_candidates 的 type 必須是 high_risk_term。")
    for candidate in schema.paragraph_merge_candidates:
        _validate_status(candidate.status)
        if candidate.type != "paragraph_merge":
            raise ValueError("paragraph_merge_candidates 的 type 必須是 paragraph_merge。")
        if candidate.auto_apply:
            raise ValueError("paragraph_merge_candidates.auto_apply 必須固定為 false。")
    # TODO: Phase 1A only keeps the schema skeleton. Review application rules are not implemented here.


def _validate_status(status: str) -> None:
    if status not in STATUS_VALUES:
        raise ValueError(f"不支援的 status：{status}")


def validate_reviewed_json_payload(payload: Any) -> list[ErrorRecord]:
    if not isinstance(payload, dict):
        return [_review_json_error("REVIEW_JSON_ROOT_INVALID", "reviewed JSON 根節點必須是物件。", "")]

    raw_chapter_candidates = payload.get("chapter_candidates", [])
    if not isinstance(raw_chapter_candidates, list):
        return [_review_json_error("CHAPTER_CANDIDATES_INVALID", "chapter_candidates 必須是清單", "")]

    raw_candidates = payload.get("review_candidates", [])
    if not isinstance(raw_candidates, list):
        return [_review_json_error("REVIEW_CANDIDATES_INVALID", "review_candidates 必須是陣列。", "")]

    for index, candidate in enumerate(raw_chapter_candidates):
        error = _validate_chapter_candidate_payload(candidate, index)
        if error is not None:
            return [error]

    for index, candidate in enumerate(raw_candidates):
        error = _validate_review_candidate_payload(candidate, index)
        if error is not None:
            return [error]
    return []


def _validate_chapter_candidate_payload(candidate: Any, index: int) -> ErrorRecord | None:
    detail_prefix = f"chapter_candidates[{index}]"
    if not isinstance(candidate, dict):
        return _review_json_error(
            "CHAPTER_CANDIDATE_INVALID",
            "chapter candidate 必須是物件",
            f"{detail_prefix} must be an object",
        )

    candidate_id = candidate.get("candidate_id")
    if not isinstance(candidate_id, str) or not candidate_id.strip():
        return _review_json_error(
            "CHAPTER_CANDIDATE_ID_INVALID",
            "chapter candidate 必須有非空白 candidate_id",
            f"{detail_prefix}.candidate_id must be a non-empty string",
        )

    candidate_type = candidate.get("type")
    if not isinstance(candidate_type, str):
        return _review_json_error(
            "CHAPTER_CANDIDATE_TYPE_INVALID",
            "chapter candidate type 必須是字串",
            f"{detail_prefix}.type must be a string",
        )

    status = candidate.get("status")
    if not isinstance(status, str) or status not in STATUS_VALUES:
        return _review_json_error(
            "CHAPTER_CANDIDATE_STATUS_INVALID",
            "chapter candidate status 不合法",
            f"{detail_prefix}.status must be a supported status enum",
        )

    paragraph_index = candidate.get("paragraph_index")
    if type(paragraph_index) is not int or paragraph_index < 0:
        return _review_json_error(
            "CHAPTER_CANDIDATE_PARAGRAPH_INDEX_INVALID",
            "chapter candidate paragraph_index 必須是非負整數",
            f"{detail_prefix}.paragraph_index must be a non-negative integer",
        )

    return None


def _validate_review_candidate_payload(candidate: Any, index: int) -> ErrorRecord | None:
    detail_prefix = f"review_candidates[{index}]"
    if not isinstance(candidate, dict):
        return _review_json_error(
            "REVIEW_CANDIDATE_INVALID",
            "review_candidates 內含格式不正確的候選項目。",
            f"{detail_prefix} 必須是物件。",
        )

    candidate_id = candidate.get("candidate_id")
    if not isinstance(candidate_id, str) or not candidate_id.strip():
        return _review_json_error(
            "REVIEW_CANDIDATE_ID_INVALID",
            "review candidate 缺少有效的 candidate_id。",
            f"{detail_prefix}.candidate_id 必須是非空字串。",
        )

    candidate_type = candidate.get("type")
    if not isinstance(candidate_type, str):
        return _review_json_error(
            "REVIEW_CANDIDATE_TYPE_INVALID",
            "review candidate type 必須是字串。",
            f"{detail_prefix}.type 必須是字串。",
        )

    status = candidate.get("status")
    if not isinstance(status, str) or status not in STATUS_VALUES:
        return _review_json_error(
            "REVIEW_CANDIDATE_STATUS_INVALID",
            "review candidate status 不支援。",
            f"{detail_prefix}.status 必須是既有 status enum。",
        )
    if status == STATUS_AUTO_ACCEPTED:
        return _review_json_error(
            "REVIEW_CANDIDATE_STATUS_INVALID",
            "review_candidates 不允許 auto_accepted。",
            f"{detail_prefix}.status 不得為 auto_accepted。",
        )

    source_text = candidate.get("source_text")
    if not isinstance(source_text, str) or not source_text:
        return _review_json_error(
            "REVIEW_CANDIDATE_SOURCE_TEXT_INVALID",
            "review candidate 缺少有效的 source_text。",
            f"{detail_prefix}.source_text 必須是非空字串。",
        )

    paragraph_index = candidate.get("paragraph_index")
    if type(paragraph_index) is not int or paragraph_index < 0:
        return _review_json_error(
            "REVIEW_CANDIDATE_PARAGRAPH_INDEX_INVALID",
            "review candidate 的 paragraph_index 必須是非負整數。",
            f"{detail_prefix}.paragraph_index 必須是非負整數。",
        )

    char_start = candidate.get("char_start")
    char_end = candidate.get("char_end")
    if type(char_start) is not int or type(char_end) is not int or char_start < 0 or char_end <= char_start:
        return _review_json_error(
            "REVIEW_CANDIDATE_SPAN_INVALID",
            "review candidate 的 char_start / char_end 範圍不正確。",
            f"{detail_prefix}.char_start / char_end 必須是整數，且 char_start >= 0、char_end > char_start。",
        )

    context_before = candidate.get("context_before")
    if context_before is not None and not isinstance(context_before, str):
        return _review_json_error(
            "REVIEW_CANDIDATE_CONTEXT_INVALID",
            "review candidate 的 context_before / context_after 必須是字串。",
            f"{detail_prefix}.context_before 必須是字串。",
        )
    context_after = candidate.get("context_after")
    if context_after is not None and not isinstance(context_after, str):
        return _review_json_error(
            "REVIEW_CANDIDATE_CONTEXT_INVALID",
            "review candidate 的 context_before / context_after 必須是字串。",
            f"{detail_prefix}.context_after 必須是字串。",
        )

    return None


def _review_json_error(code: str, message: str, technical_detail: str) -> ErrorRecord:
    return ErrorRecord(code=code, message=message, technical_detail=technical_detail)
