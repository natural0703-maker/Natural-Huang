from __future__ import annotations

from dataclasses import dataclass, field
from hashlib import sha256
from typing import Literal

from src.frozen_spec_v1 import STATUS_AUTO_ACCEPTED, STATUS_VALUES


Status = Literal["pending", "accepted", "rejected", "skip", "auto_accepted"]


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
