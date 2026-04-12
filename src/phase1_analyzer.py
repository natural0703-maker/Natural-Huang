from __future__ import annotations

import re
from hashlib import sha256
from pathlib import Path

from docx import Document

from src.phase1_config import Phase1ConfigCheck
from src.review_schema import (
    ChapterCandidate,
    ErrorRecord,
    ParagraphMergeCandidate,
    ReviewCandidate,
    ReviewSchema,
    make_chapter_candidate_id,
    make_paragraph_merge_candidate_id,
    make_review_candidate_id,
)
from src.rule_loader import load_high_risk_rules


CONTEXT_WINDOW = 12
MIN_MERGE_PREV_LEN = 8
MIN_MERGE_NEXT_LEN = 4

_SENTENCE_ENDINGS = ("。", "！", "？", "；", "：", "」", "』", '"', "”", "……", "——")
_DIALOGUE_STARTS = ("「", "『", "“", '"', "—", "--")
_NEXT_PARAGRAPH_BLOCK_STARTS = ("「", "『", "（", "(", "【", "[")

_CHAPTER_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    (
        "cn_arabic_chapter",
        re.compile(r"^第\s*\d+\s*章(?:[：:\s].{1,30})?$"),
    ),
    (
        "cn_numeric_chapter",
        re.compile(r"^第\s*[零〇一二三四五六七八九十百千兩]+章(?:[：:\s].{1,30})?$"),
    ),
    (
        "special_chapter",
        re.compile(r"^(序章|楔子|番外|後記)$"),
    ),
    (
        "en_chapter",
        re.compile(r"^Chapter\s+\d+(?:[：:\s].{1,30})?$", re.IGNORECASE),
    ),
)


def analyze_docx(input_path: Path, config_check: Phase1ConfigCheck) -> ReviewSchema:
    if not input_path.exists():
        return _schema_with_error("INPUT_NOT_FOUND", f"找不到輸入檔：{input_path}", str(input_path))
    if input_path.suffix.lower() != ".docx":
        return _schema_with_error("INPUT_NOT_DOCX", f"輸入檔不是 .docx：{input_path}", str(input_path))

    try:
        document = Document(input_path)
    except Exception as exc:
        return _schema_with_error("DOCX_READ_FAILED", f"無法讀取 DOCX：{input_path}", str(exc))

    paragraphs = [paragraph.text.strip() for paragraph in document.paragraphs]
    review_candidates = _detect_review_candidates(paragraphs, config_check)
    high_risk_paragraphs = {candidate.paragraph_index for candidate in review_candidates}
    schema = ReviewSchema(
        chapter_candidates=_detect_chapter_candidates(paragraphs),
        review_candidates=review_candidates,
        paragraph_merge_candidates=_detect_paragraph_merge_candidates(paragraphs, high_risk_paragraphs),
    )
    return schema


def _detect_chapter_candidates(paragraphs: list[str]) -> list[ChapterCandidate]:
    candidates: list[ChapterCandidate] = []
    for paragraph_index, text in enumerate(paragraphs):
        if not text:
            continue
        for rule_id, pattern in _CHAPTER_PATTERNS:
            if not pattern.match(text):
                continue
            candidates.append(
                ChapterCandidate(
                    candidate_id=make_chapter_candidate_id(paragraph_index, rule_id, text),
                    status="pending",
                    source_text=text,
                    resolved_text="",
                    normalized_title=text,
                    paragraph_index=paragraph_index,
                    matched_rule_id=rule_id,
                    confidence=0.8,
                    auto_accept=False,
                )
            )
            break
    return candidates


def _detect_review_candidates(paragraphs: list[str], config_check: Phase1ConfigCheck) -> list[ReviewCandidate]:
    rules = [rule for rule in load_high_risk_rules(config_check.config.default_high_risk_rules_path) if rule.enabled]
    candidates: list[ReviewCandidate] = []
    for paragraph_index, text in enumerate(paragraphs):
        if not text:
            continue
        for rule in rules:
            start = 0
            while True:
                char_start = text.find(rule.term, start)
                if char_start < 0:
                    break
                char_end = char_start + len(rule.term)
                candidates.append(
                    ReviewCandidate(
                        candidate_id=make_review_candidate_id(
                            _rule_id(rule.term, rule.risk_category),
                            paragraph_index,
                            char_start,
                            rule.term,
                        ),
                        status="pending",
                        source_text=rule.term,
                        resolved_text="",
                        rule_id=_rule_id(rule.term, rule.risk_category),
                        paragraph_index=paragraph_index,
                        char_start=char_start,
                        char_end=char_end,
                        context_before=text[max(0, char_start - CONTEXT_WINDOW) : char_start],
                        context_after=text[char_end : char_end + CONTEXT_WINDOW],
                        risk_category=rule.risk_category,
                    )
                )
                start = char_end
    return candidates


def _detect_paragraph_merge_candidates(
    paragraphs: list[str],
    high_risk_paragraphs: set[int],
) -> list[ParagraphMergeCandidate]:
    candidates: list[ParagraphMergeCandidate] = []
    for paragraph_index in range(len(paragraphs) - 1):
        current = paragraphs[paragraph_index]
        next_text = paragraphs[paragraph_index + 1]
        if not _should_collect_merge_candidate(
            current=current,
            next_text=next_text,
            paragraph_index=paragraph_index,
            next_paragraph_index=paragraph_index + 1,
            high_risk_paragraphs=high_risk_paragraphs,
        ):
            continue
        candidates.append(
            ParagraphMergeCandidate(
                candidate_id=make_paragraph_merge_candidate_id(paragraph_index, paragraph_index + 1, current),
                status="pending",
                paragraph_index=paragraph_index,
                next_paragraph_index=paragraph_index + 1,
                source_text=current,
                next_text=next_text,
                auto_apply=False,
                reason="前段未以常見句末標點結尾，且下一段不像章節或對話段落。",
            )
        )
    return candidates


def _should_collect_merge_candidate(
    *,
    current: str,
    next_text: str,
    paragraph_index: int,
    next_paragraph_index: int,
    high_risk_paragraphs: set[int],
) -> bool:
    if not current or not next_text:
        return False
    if paragraph_index in high_risk_paragraphs or next_paragraph_index in high_risk_paragraphs:
        return False
    if len(current) < MIN_MERGE_PREV_LEN or len(next_text) < MIN_MERGE_NEXT_LEN:
        return False
    if _is_plain_symbols_or_digits(current) or _is_plain_symbols_or_digits(next_text):
        return False
    if _looks_like_chapter_title(current) or _looks_like_chapter_title(next_text):
        return False
    if _looks_like_dialogue(current) or _looks_like_dialogue(next_text):
        return False
    if next_text.startswith(_NEXT_PARAGRAPH_BLOCK_STARTS):
        return False
    if current.endswith(_SENTENCE_ENDINGS):
        return False
    return True


def _looks_like_chapter_title(text: str) -> bool:
    return any(pattern.match(text) for _, pattern in _CHAPTER_PATTERNS)


def _looks_like_dialogue(text: str) -> bool:
    return text.startswith(_DIALOGUE_STARTS)


def _is_plain_symbols_or_digits(text: str) -> bool:
    return bool(re.fullmatch(r"[\W\d_]+", text, flags=re.UNICODE))


def _rule_id(term: str, risk_category: str) -> str:
    normalized_category = re.sub(r"[^0-9a-zA-Z_]+", "_", risk_category.strip().lower()).strip("_")
    if not normalized_category:
        normalized_category = "risk"
    digest = sha256(f"{risk_category}\n{term}".encode("utf-8")).hexdigest()[:12]
    return f"{normalized_category}:{digest}"


def _schema_with_error(code: str, message: str, technical_detail: str) -> ReviewSchema:
    return ReviewSchema(
        errors=[
            ErrorRecord(
                code=code,
                message=message,
                technical_detail=technical_detail,
            )
        ]
    )
