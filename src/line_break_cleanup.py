from __future__ import annotations

from dataclasses import dataclass


LINE_BREAK_JOINED = "LINE_BREAK_JOINED"
LINE_BREAK_SKIPPED_SENTENCE_END = "LINE_BREAK_SKIPPED_SENTENCE_END"
LINE_BREAK_SKIPPED_BLANK_LINE = "LINE_BREAK_SKIPPED_BLANK_LINE"
LINE_BREAK_SKIPPED_LIST_LIKE = "LINE_BREAK_SKIPPED_LIST_LIKE"
LINE_BREAK_SKIPPED_SHORT_LINES = "LINE_BREAK_SKIPPED_SHORT_LINES"
LINE_BREAK_SKIPPED_UNSAFE_BOUNDARY = "LINE_BREAK_SKIPPED_UNSAFE_BOUNDARY"

_SENTENCE_END_CHARS = set("。！？!?」』”’…；;")
_JOINABLE_PREVIOUS_END_CHARS = set("，、")
_LIST_PREFIXES = ("-", "•", "*")
_UNSAFE_NEXT_START_CHARS = set("「『\"'“‘")
_UNSAFE_PREVIOUS_END_CHARS = set("：:")


@dataclass(frozen=True)
class LineBreakCleanupResult:
    text: str
    applied_count: int
    skipped_count: int
    codes: dict[str, int]


def cleanup_inline_line_breaks(text: str) -> LineBreakCleanupResult:
    """Conservatively remove obvious non-semantic hard line breaks in plain text."""
    if "\n" not in text and "\r" not in text:
        return LineBreakCleanupResult(text=text, applied_count=0, skipped_count=0, codes={})

    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    lines = normalized.split("\n")
    output = lines[0]
    codes: dict[str, int] = {}
    applied_count = 0
    skipped_count = 0

    for next_line in lines[1:]:
        decision = _classify_boundary(output, next_line)
        _increment(codes, decision)
        if decision == LINE_BREAK_JOINED:
            output = output.rstrip() + next_line.lstrip()
            applied_count += 1
        else:
            output += "\n" + next_line
            skipped_count += 1

    return LineBreakCleanupResult(
        text=output,
        applied_count=applied_count,
        skipped_count=skipped_count,
        codes=codes,
    )


def _classify_boundary(current_text: str, next_line: str) -> str:
    previous_line = current_text.split("\n")[-1]
    previous = previous_line.strip()
    following = next_line.strip()

    if not previous or not following:
        return LINE_BREAK_SKIPPED_BLANK_LINE
    if _is_list_like(previous) or _is_list_like(following):
        return LINE_BREAK_SKIPPED_LIST_LIKE
    if _looks_like_short_line_pair(previous, following):
        return LINE_BREAK_SKIPPED_SHORT_LINES

    previous_char = previous[-1]
    following_char = following[0]
    if previous_char in _SENTENCE_END_CHARS:
        return LINE_BREAK_SKIPPED_SENTENCE_END
    if previous_char in _UNSAFE_PREVIOUS_END_CHARS or following_char in _UNSAFE_NEXT_START_CHARS:
        return LINE_BREAK_SKIPPED_UNSAFE_BOUNDARY
    if previous_char in _JOINABLE_PREVIOUS_END_CHARS and _is_cjk(following_char):
        return LINE_BREAK_JOINED
    if _is_cjk(previous_char) and _is_cjk(following_char):
        return LINE_BREAK_JOINED
    return LINE_BREAK_SKIPPED_UNSAFE_BOUNDARY


def _is_list_like(line: str) -> bool:
    stripped = line.strip()
    if not stripped:
        return False
    if stripped.startswith(_LIST_PREFIXES):
        return True
    if len(stripped) >= 2 and stripped[0].isdigit() and stripped[1] in {".", "、", ")"}:
        return True
    if len(stripped) >= 3 and stripped[0] == "(" and stripped[1].isdigit() and stripped[2] == ")":
        return True
    if len(stripped) >= 2 and _is_cjk_number(stripped[0]) and stripped[1] in {"、", "."}:
        return True
    if len(stripped) >= 3 and stripped[0] in {"（", "("} and _is_cjk_number(stripped[1]) and stripped[2] in {"）", ")"}:
        return True
    return False


def _looks_like_short_line_pair(previous: str, following: str) -> bool:
    if len(previous) > 7 or len(following) > 7:
        return False
    if len(previous) < 4 or len(following) < 4:
        return False
    if any(char in previous + following for char in "，、,."):
        return False
    return all(_is_cjk(char) for char in previous) and all(_is_cjk(char) for char in following)


def _is_cjk(char: str) -> bool:
    if not char:
        return False
    code = ord(char)
    return (
        0x3400 <= code <= 0x4DBF
        or 0x4E00 <= code <= 0x9FFF
        or 0xF900 <= code <= 0xFAFF
    )


def _is_cjk_number(char: str) -> bool:
    return char in set("一二三四五六七八九十壹貳參肆伍陸柒捌玖拾")


def _increment(codes: dict[str, int], code: str) -> None:
    codes[code] = codes.get(code, 0) + 1
