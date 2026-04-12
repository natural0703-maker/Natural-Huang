from __future__ import annotations

from collections import defaultdict

import regex

from src.models import ReviewCandidateRecord
from src.risk_terms import DEFAULT_HIGH_RISK_RULES
from src.rule_loader import (
    build_high_risk_category_map,
    build_high_risk_suggestion_map,
    build_high_risk_term_list,
)


DEFAULT_HIGH_RISK_TERMS: list[str] = build_high_risk_term_list(DEFAULT_HIGH_RISK_RULES)
RISK_CATEGORY_MAP: dict[str, str] = build_high_risk_category_map(DEFAULT_HIGH_RISK_RULES)
SUGGESTION_MAP: dict[str, str] = build_high_risk_suggestion_map(DEFAULT_HIGH_RISK_RULES)

LOW_CONFIDENCE_TERMS = {"得", "的", "地", "裡", "裏", "於", "在"}


def _build_context_snippet(text: str, start: int, end: int, radius: int = 12) -> str:
    left = max(0, start - radius)
    right = min(len(text), end + radius)
    return text[left:right]


def _build_candidate_id(file_name: str, paragraph_index: int, hit_index: int) -> str:
    safe_file = file_name.replace(" ", "_")
    return f"{safe_file}-P{paragraph_index:05d}-C{hit_index:03d}"


def detect_high_risk_terms(
    text: str,
    paragraph_index: int,
    file_name: str,
    terms: list[str] | None = None,
    category_map: dict[str, str] | None = None,
    suggestion_map: dict[str, str] | None = None,
    original_text: str | None = None,
    chapter_guess: str = "",
) -> list[ReviewCandidateRecord]:
    active_terms = terms if terms is not None else DEFAULT_HIGH_RISK_TERMS
    active_category_map = category_map if category_map is not None else RISK_CATEGORY_MAP
    active_suggestion_map = suggestion_map if suggestion_map is not None else SUGGESTION_MAP
    if not active_terms:
        return []

    ordered_terms = sorted(active_terms, key=len, reverse=True)
    pattern = regex.compile("|".join(regex.escape(term) for term in ordered_terms))
    source_text = original_text if original_text is not None else text

    per_paragraph_counter: dict[str, int] = defaultdict(int)
    candidates: list[ReviewCandidateRecord] = []

    for match in pattern.finditer(text):
        hit_term = match.group(0)
        per_paragraph_counter["all"] += 1
        hit_index = per_paragraph_counter["all"]
        candidate_id = _build_candidate_id(file_name, paragraph_index, hit_index)

        candidates.append(
            ReviewCandidateRecord(
                file_name=file_name,
                paragraph_index=paragraph_index,
                hit_term=hit_term,
                risk_category=active_category_map.get(hit_term, "wording"),
                original_snippet=_build_context_snippet(source_text, match.start(), match.end()),
                processed_snippet=_build_context_snippet(text, match.start(), match.end()),
                context_snippet=_build_context_snippet(text, match.start(), match.end()),
                suggested_candidates=active_suggestion_map.get(hit_term, "請人工確認"),
                confidence=0.35 if hit_term in LOW_CONFIDENCE_TERMS else 0.55,
                status="pending",
                note="",
                candidate_id=candidate_id,
                chapter_guess=chapter_guess,
                position_hint=f"段落 {paragraph_index}（第 {hit_index} 處）",
                resolved_text="",
            )
        )

    return candidates
