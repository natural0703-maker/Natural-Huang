from __future__ import annotations

import regex


_WHITELIST = {
    "序章",
    "楔子",
    "終章",
    "後記",
    "番外",
    "尾聲",
}


_CHAPTER_PATTERN = regex.compile(
    r"^\s*第[零〇一二三四五六七八九十百千萬兩两\d]+[章節回](?:[\s\u3000]*[:：]?\s*.*)?$"
)


def is_direct_chapter_heading(text: str) -> bool:
    normalized = text.strip()
    if not normalized:
        return False
    if normalized in _WHITELIST:
        return True
    return bool(_CHAPTER_PATTERN.match(normalized))
