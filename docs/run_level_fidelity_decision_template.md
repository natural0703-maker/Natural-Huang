# Run-Level Fidelity H-3 Decision Template

用途：根據 coverage estimator 結果、人工盤點或人工 Word 檢查結果，判斷 run-level fidelity 是否值得進入 H-3 規劃。

本模板只支援三種決策：

- `Go`
- `Prototype only`
- `No-go`

本模板不代表已決定接入 `apply_review()`，也不代表 H-3 一定會實作。

## Basic Info

| Field | Type | Required | Value |
|---|---|---:|---|
| `decision_id` | short text | yes |  |
| `date` | short text (`YYYY-MM-DD`) | yes |  |
| `reviewer` | short text | no |  |
| `sample_set_name` | short text | yes |  |
| `sample_doc_count` | number | yes |  |
| `reviewed_json_count` | number | yes |  |
| `notes` | short text | no |  |

## Coverage

| Field | Type | Required | Value |
|---|---|---:|---|
| `total_candidates_count` | number | no |  |
| `total_accepted_replacements` | number | yes |  |
| `eligible_replacements_count` | number | yes |  |
| `excluded_candidates_count` | number | no |  |
| `single_run_safe_count` | number | yes |  |
| `safe_coverage_rate` | percent | yes |  |
| `practical_safe_count` | number | no |  |
| `practical_coverage_rate` | percent | no |  |
| `unsafe_count` | number | yes |  |
| `unsafe_rate` | percent | yes |  |

## Skip / Unsafe Distribution

| Field | Type | Required | Value |
|---|---|---:|---|
| `multi_run_unsafe_count` | number | no |  |
| `line_break_unsafe_count` | number | no |  |
| `expected_text_mismatch_count` | number | no |  |
| `span_not_found_count` | number | no |  |
| `invalid_span_count` | number | no |  |
| `unsupported_structure_count` | number | no |  |
| `multi_run_unsafe_is_largest_bucket` | boolean (`true` / `false`) | yes |  |
| `skip_reason_distribution_summary` | short text | no |  |

## Risk / Cost

| Field | Type | Required | Value |
|---|---|---:|---|
| `explainability_risk` | enum (`low` / `medium` / `high`) | yes |  |
| `fallback_complexity` | enum (`low` / `medium` / `high`) | yes |  |
| `maintenance_cost` | enum (`low` / `medium` / `high`) | yes |  |
| `user_visible_benefit` | enum (`low` / `medium` / `high`) | yes |  |
| `manual_word_check_required` | boolean (`true` / `false`) | no |  |
| `manual_word_check_passed` | enum (`true` / `false` / `not_run`) | yes |  |

## Decision

| Field | Type | Required | Value |
|---|---|---:|---|
| `decision` | enum (`Go` / `Prototype only` / `No-go`) | yes |  |
| `required_next_step` | enum | yes |  |

`required_next_step` only allows:

- `plan_h3_apply_review_integration`
- `collect_more_samples`
- `run_manual_word_check`
- `keep_prototype_only`
- `stop_run_fidelity_track`
- `revise_estimator_method`

## Decision Reason

- Coverage:
- Risk:
- Cost:
- Decision:

`decision_reason` rules:

- Must reference at least two quantitative indicators.
- Must mention one main risk.
- Must explain why the decision is `Go`, `Prototype only`, or `No-go`.
- Must not promise H-3 implementation.

## Go Eligibility Gate

If any of the following fields are missing, the decision must not be `Go`; the strongest allowed decision is `Prototype only`.

- `safe_coverage_rate`
- `unsafe_rate`
- `multi_run_unsafe_is_largest_bucket`
- `fallback_complexity`
- `maintenance_cost`
- `user_visible_benefit`
- `manual_word_check_passed`

Suggested `Go` threshold:

- `safe_coverage_rate >= 40%`
- `practical_coverage_rate >= 20%` when available
- `unsafe_rate <= 50%`
- `multi_run_unsafe_is_largest_bucket == false`
- `explainability_risk != high`
- `fallback_complexity != high`
- `maintenance_cost != high`
- `user_visible_benefit >= medium`
- `manual_word_check_passed == true`

## Open Questions

-

## Follow-Up Notes

-
