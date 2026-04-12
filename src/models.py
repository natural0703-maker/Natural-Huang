from dataclasses import dataclass


@dataclass(frozen=True)
class ReplacementRecord:
    paragraph_index: int
    original_snippet: str
    replaced_term: str
    target_term: str
    replacement_count: int
    file_name: str = ""


@dataclass(frozen=True)
class ReviewCandidateRecord:
    file_name: str
    paragraph_index: int
    hit_term: str
    risk_category: str
    original_snippet: str
    processed_snippet: str
    context_snippet: str
    suggested_candidates: str
    confidence: float
    status: str = "pending"
    note: str = ""
    candidate_id: str = ""
    chapter_guess: str = ""
    position_hint: str = ""
    resolved_text: str = ""


@dataclass(frozen=True)
class AnomalyRecord:
    file_name: str
    paragraph_index: int
    anomaly_char: str
    original_snippet: str
    converted_snippet: str


@dataclass(frozen=True)
class FailureRecord:
    file_name: str
    error_type: str
    error_message: str


@dataclass(frozen=True)
class SummaryRecord:
    file_name: str
    status: str
    paragraph_count: int
    total_replacements: int
    total_review_candidates: int
    total_anomalies: int
    elapsed_time_sec: float
    review_grammar_count: int = 0
    review_wording_count: int = 0
    review_regional_usage_count: int = 0
    output_file: str = ""


@dataclass(frozen=True)
class ReviewDecisionRecord:
    candidate_id: str
    file_name: str
    paragraph_index: int
    hit_term: str
    context_snippet: str
    status: str
    resolved_text: str
    note: str = ""
    chapter_guess: str = ""
    risk_category: str = ""
    suggested_candidates: str = ""
    confidence: float = 0.0


@dataclass(frozen=True)
class ApplyFailureRecord:
    file_name: str
    candidate_id: str
    error_type: str
    error_message: str


@dataclass(frozen=True)
class ApplyDecisionResultRecord:
    file_name: str
    candidate_id: str
    paragraph_index: int
    status: str
    applied: bool
    reason: str
    hit_term: str
    resolved_text: str


@dataclass(frozen=True)
class ApplySummaryRecord:
    file_name: str
    source_file: str
    output_file: str
    total_candidates: int
    applied_count: int
    skipped_count: int
    not_found_count: int
    conflict_count: int
    failed_count: int
