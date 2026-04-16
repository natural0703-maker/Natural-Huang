from __future__ import annotations

from dataclasses import dataclass
from typing import Any


RUN_REPLACE_APPLIED = "RUN_REPLACE_APPLIED"
RUN_REPLACE_INVALID_SPAN = "RUN_REPLACE_INVALID_SPAN"
RUN_REPLACE_EMPTY_REPLACEMENT = "RUN_REPLACE_EMPTY_REPLACEMENT"
RUN_REPLACE_EXPECTED_TEXT_MISMATCH = "RUN_REPLACE_EXPECTED_TEXT_MISMATCH"
RUN_REPLACE_SPAN_NOT_FOUND = "RUN_REPLACE_SPAN_NOT_FOUND"
RUN_REPLACE_SPANS_MULTIPLE_RUNS = "RUN_REPLACE_SPANS_MULTIPLE_RUNS"
RUN_REPLACE_UNSAFE_LINE_BREAK = "RUN_REPLACE_UNSAFE_LINE_BREAK"


@dataclass(frozen=True)
class RunReplaceResult:
    status: str
    code: str
    matched_text: str = ""
    replacement_text: str = ""
    message: str = ""


def try_replace_text_in_single_run(
    paragraph: Any,
    char_start: int,
    char_end: int,
    replacement_text: str,
    *,
    expected_text: str | None = None,
) -> RunReplaceResult:
    """Replace text only when the target span is fully inside one run."""
    paragraph_text = str(getattr(paragraph, "text", ""))
    if (
        not isinstance(char_start, int)
        or not isinstance(char_end, int)
        or char_start < 0
        or char_end <= char_start
        or char_end > len(paragraph_text)
    ):
        return RunReplaceResult(
            status="invalid",
            code=RUN_REPLACE_INVALID_SPAN,
            message="Invalid paragraph character span.",
        )

    if replacement_text == "":
        return RunReplaceResult(
            status="invalid",
            code=RUN_REPLACE_EMPTY_REPLACEMENT,
            message="Replacement text must not be empty.",
        )

    matched_text = paragraph_text[char_start:char_end]
    if expected_text is not None and matched_text != expected_text:
        return RunReplaceResult(
            status="skipped",
            code=RUN_REPLACE_EXPECTED_TEXT_MISMATCH,
            matched_text=matched_text,
            replacement_text=replacement_text,
            message="Matched text does not equal expected text.",
        )

    runs = list(getattr(paragraph, "runs", []) or [])
    start_location: tuple[int, int] | None = None
    end_location: tuple[int, int] | None = None
    offset = 0
    for index, run in enumerate(runs):
        run_text = str(getattr(run, "text", ""))
        run_start = offset
        run_end = run_start + len(run_text)
        if run_start <= char_start < run_end:
            start_location = (index, char_start - run_start)
        if run_start < char_end <= run_end:
            end_location = (index, char_end - run_start)
        offset = run_end

    if start_location is None or end_location is None:
        return RunReplaceResult(
            status="skipped",
            code=RUN_REPLACE_SPAN_NOT_FOUND,
            matched_text=matched_text,
            replacement_text=replacement_text,
            message="Target span could not be mapped to document runs.",
        )

    start_run_index, run_char_start = start_location
    end_run_index, run_char_end = end_location
    if start_run_index != end_run_index:
        return RunReplaceResult(
            status="unsafe",
            code=RUN_REPLACE_SPANS_MULTIPLE_RUNS,
            matched_text=matched_text,
            replacement_text=replacement_text,
            message="Target span crosses multiple runs.",
        )

    run = runs[start_run_index]
    run_text = str(run.text)
    if "\n" in run_text or "\r" in run_text:
        return RunReplaceResult(
            status="unsafe",
            code=RUN_REPLACE_UNSAFE_LINE_BREAK,
            matched_text=matched_text,
            replacement_text=replacement_text,
            message="Target run contains a line break.",
        )

    run.text = run_text[:run_char_start] + replacement_text + run_text[run_char_end:]

    return RunReplaceResult(
        status="applied",
        code=RUN_REPLACE_APPLIED,
        matched_text=matched_text,
        replacement_text=replacement_text,
    )
