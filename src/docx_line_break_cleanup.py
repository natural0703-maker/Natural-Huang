from __future__ import annotations

import re
from dataclasses import dataclass, field

from src.line_break_cleanup import cleanup_inline_line_breaks


LINE_BREAK_CLEANUP_ELIGIBLE = "LINE_BREAK_CLEANUP_ELIGIBLE"
LINE_BREAK_CLEANUP_SKIPPED_EMPTY = "LINE_BREAK_CLEANUP_SKIPPED_EMPTY"
LINE_BREAK_CLEANUP_SKIPPED_NO_LINE_BREAK = "LINE_BREAK_CLEANUP_SKIPPED_NO_LINE_BREAK"
LINE_BREAK_CLEANUP_SKIPPED_TABLE_CELL = "LINE_BREAK_CLEANUP_SKIPPED_TABLE_CELL"
LINE_BREAK_CLEANUP_SKIPPED_HEADING = "LINE_BREAK_CLEANUP_SKIPPED_HEADING"
LINE_BREAK_CLEANUP_SKIPPED_LIST_LIKE = "LINE_BREAK_CLEANUP_SKIPPED_LIST_LIKE"
LINE_BREAK_CLEANUP_SKIPPED_NON_CJK_DOMINANT = "LINE_BREAK_CLEANUP_SKIPPED_NON_CJK_DOMINANT"
LINE_BREAK_CLEANUP_SKIPPED_DIALOGUE_LIKE = "LINE_BREAK_CLEANUP_SKIPPED_DIALOGUE_LIKE"
LINE_BREAK_CLEANUP_SKIPPED_SPECIAL_STRUCTURE = "LINE_BREAK_CLEANUP_SKIPPED_SPECIAL_STRUCTURE"

_LIST_PREFIX_RE = re.compile(
    r"^\s*(?:[-*•]|[0-9]+[.)、]|[(（][0-9]+[)）]|[一二三四五六七八九十]+[、.．])"
)
_HEADING_STYLE_PREFIXES = ("heading", "標題")
_SPECIAL_XML_NAMES = {
    "hyperlink",
    "fldChar",
    "instrText",
    "sdt",
    "commentRangeStart",
    "commentRangeEnd",
    "bookmarkStart",
    "bookmarkEnd",
    "ins",
    "del",
}
_DIALOGUE_START_CHARS = set("「『“\"'")


@dataclass(frozen=True)
class ParagraphCleanupEligibility:
    eligible: bool
    code: str
    reason: str = ""


@dataclass(frozen=True)
class ParagraphCleanupApplyResult:
    changed: bool
    eligibility_code: str
    cleanup_applied_count: int
    cleanup_skipped_count: int
    reason: str = ""


@dataclass(frozen=True)
class DocumentLineBreakCleanupSummary:
    scanned_count: int = 0
    eligible_count: int = 0
    changed_count: int = 0
    skipped_count: int = 0
    codes: dict[str, int] = field(default_factory=dict)


def assess_paragraph_for_line_break_cleanup(paragraph) -> ParagraphCleanupEligibility:
    """Return whether a python-docx paragraph is safe to consider for cleanup.

    This selector is intentionally read-only. It only decides whether a paragraph
    looks like ordinary body text; it does not modify the document or call the
    text cleanup helper.
    """
    text = paragraph.text
    if not text.strip():
        return _skipped(LINE_BREAK_CLEANUP_SKIPPED_EMPTY, "paragraph is empty")
    if "\n" not in text and "\r" not in text:
        return _skipped(LINE_BREAK_CLEANUP_SKIPPED_NO_LINE_BREAK, "paragraph has no hard line break")
    if _is_inside_table_cell(paragraph):
        return _skipped(LINE_BREAK_CLEANUP_SKIPPED_TABLE_CELL, "paragraph is inside a table cell")
    if _is_heading(paragraph):
        return _skipped(LINE_BREAK_CLEANUP_SKIPPED_HEADING, "paragraph style is heading-like")
    if _is_list_like(paragraph):
        return _skipped(LINE_BREAK_CLEANUP_SKIPPED_LIST_LIKE, "paragraph looks like a list")
    if _has_special_structure(paragraph):
        return _skipped(
            LINE_BREAK_CLEANUP_SKIPPED_SPECIAL_STRUCTURE,
            "paragraph contains unsupported Word XML structure",
        )
    if _looks_dialogue_like(text):
        return _skipped(LINE_BREAK_CLEANUP_SKIPPED_DIALOGUE_LIKE, "paragraph looks dialogue-like")
    if not _is_cjk_dominant(text):
        return _skipped(
            LINE_BREAK_CLEANUP_SKIPPED_NON_CJK_DOMINANT,
            "paragraph is not CJK-dominant",
        )
    return ParagraphCleanupEligibility(
        eligible=True,
        code=LINE_BREAK_CLEANUP_ELIGIBLE,
        reason="ordinary CJK paragraph with hard line break",
    )


def apply_line_break_cleanup_to_paragraph(paragraph) -> ParagraphCleanupApplyResult:
    """Apply plain-text line-break cleanup to one eligible paragraph.

    This is still an isolated prototype. It does not save the document, does not
    scan other paragraphs, and is not wired into convert/apply_review.
    """
    eligibility = assess_paragraph_for_line_break_cleanup(paragraph)
    if not eligibility.eligible:
        return ParagraphCleanupApplyResult(
            changed=False,
            eligibility_code=eligibility.code,
            cleanup_applied_count=0,
            cleanup_skipped_count=0,
            reason=eligibility.reason,
        )

    original_text = paragraph.text
    cleanup = cleanup_inline_line_breaks(original_text)
    if cleanup.applied_count <= 0 or cleanup.text == original_text:
        return ParagraphCleanupApplyResult(
            changed=False,
            eligibility_code=eligibility.code,
            cleanup_applied_count=cleanup.applied_count,
            cleanup_skipped_count=cleanup.skipped_count,
            reason="cleanup produced no text change",
        )

    paragraph.text = cleanup.text
    return ParagraphCleanupApplyResult(
        changed=True,
        eligibility_code=eligibility.code,
        cleanup_applied_count=cleanup.applied_count,
        cleanup_skipped_count=cleanup.skipped_count,
        reason="paragraph text cleaned",
    )


def apply_line_break_cleanup_to_document(document) -> DocumentLineBreakCleanupSummary:
    """Apply line-break cleanup to eligible body paragraphs in a document.

    This helper is intentionally small and conservative. It only walks
    ``document.paragraphs`` and delegates paragraph safety checks to
    ``apply_line_break_cleanup_to_paragraph``.
    """
    scanned_count = 0
    eligible_count = 0
    changed_count = 0
    skipped_count = 0
    codes: dict[str, int] = {}

    for paragraph in document.paragraphs:
        scanned_count += 1
        result = apply_line_break_cleanup_to_paragraph(paragraph)
        _increment(codes, result.eligibility_code)

        if result.eligibility_code == LINE_BREAK_CLEANUP_ELIGIBLE:
            eligible_count += 1
            if result.changed:
                changed_count += 1
            else:
                skipped_count += 1
        else:
            skipped_count += 1

    return DocumentLineBreakCleanupSummary(
        scanned_count=scanned_count,
        eligible_count=eligible_count,
        changed_count=changed_count,
        skipped_count=skipped_count,
        codes=codes,
    )


def _skipped(code: str, reason: str) -> ParagraphCleanupEligibility:
    return ParagraphCleanupEligibility(eligible=False, code=code, reason=reason)


def _increment(codes: dict[str, int], code: str) -> None:
    codes[code] = codes.get(code, 0) + 1


def _is_inside_table_cell(paragraph) -> bool:
    return any(_local_name(element) == "tc" for element in paragraph._p.iterancestors())


def _is_heading(paragraph) -> bool:
    style = getattr(paragraph, "style", None)
    style_name = (getattr(style, "name", "") or "").strip().lower()
    style_id = (getattr(style, "style_id", "") or "").strip().lower()
    return style_name.startswith(_HEADING_STYLE_PREFIXES) or style_id.startswith("heading")


def _is_list_like(paragraph) -> bool:
    if paragraph._p.pPr is not None and paragraph._p.pPr.numPr is not None:
        return True

    style = getattr(paragraph, "style", None)
    style_name = (getattr(style, "name", "") or "").strip().lower()
    if "list" in style_name or "bullet" in style_name:
        return True

    lines = [line.strip() for line in paragraph.text.replace("\r\n", "\n").replace("\r", "\n").split("\n")]
    return any(_LIST_PREFIX_RE.match(line) for line in lines if line)


def _has_special_structure(paragraph) -> bool:
    ancestors = {_local_name(element) for element in paragraph._p.iterancestors()}
    if ancestors & {"sdt", "ins", "del"}:
        return True
    return any(_local_name(element) in _SPECIAL_XML_NAMES for element in paragraph._p.iter())


def _looks_dialogue_like(text: str) -> bool:
    lines = [line.strip() for line in text.replace("\r\n", "\n").replace("\r", "\n").split("\n") if line.strip()]
    if len(lines) < 2:
        return False
    dialogue_like = 0
    for line in lines:
        if line[0] in _DIALOGUE_START_CHARS or line.endswith(("」", "』", '"', "'")):
            dialogue_like += 1
    return dialogue_like == len(lines)


def _is_cjk_dominant(text: str) -> bool:
    cjk_count = sum(1 for char in text if _is_cjk(char))
    latin_count = sum(1 for char in text if ("A" <= char <= "Z") or ("a" <= char <= "z"))
    return cjk_count >= 2 and cjk_count >= latin_count


def _is_cjk(char: str) -> bool:
    code = ord(char)
    return (
        0x3400 <= code <= 0x4DBF
        or 0x4E00 <= code <= 0x9FFF
        or 0xF900 <= code <= 0xFAFF
    )


def _local_name(element) -> str:
    tag = getattr(element, "tag", "")
    if "}" in tag:
        return tag.rsplit("}", 1)[1]
    return tag
