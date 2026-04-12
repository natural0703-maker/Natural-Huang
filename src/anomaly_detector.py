from __future__ import annotations

from src.models import AnomalyRecord


DEFAULT_ANOMALY_CHARS: list[str] = [
    "?",
    "\uFFFD",
    "\u200B",
    "\u200C",
    "\u200D",
    "\u200E",
    "\u200F",
    "\u2060",
    "\uFEFF",
]


def _snippet_by_index(text: str, index: int, radius: int = 12) -> str:
    left = max(0, index - radius)
    right = min(len(text), index + radius + 1)
    return text[left:right]


def detect_anomalies(
    original_text: str,
    converted_text: str,
    paragraph_index: int,
    file_name: str,
    anomaly_chars: list[str] | None = None,
) -> list[AnomalyRecord]:
    active_chars = anomaly_chars if anomaly_chars is not None else DEFAULT_ANOMALY_CHARS
    records: list[AnomalyRecord] = []
    if not active_chars:
        return records

    for idx, char in enumerate(converted_text):
        if char in active_chars:
            original_snippet = _snippet_by_index(original_text, min(idx, max(0, len(original_text) - 1)))
            converted_snippet = _snippet_by_index(converted_text, idx)
            records.append(
                AnomalyRecord(
                    file_name=file_name,
                    paragraph_index=paragraph_index,
                    anomaly_char=char,
                    original_snippet=original_snippet,
                    converted_snippet=converted_snippet,
                )
            )
    return records

