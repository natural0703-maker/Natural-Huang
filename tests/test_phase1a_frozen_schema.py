import pytest

from src.frozen_spec_v1 import (
    BODY_FIRST_LINE_INDENT_PT,
    BODY_FONT_SIZE_PT,
    FONT_NAME,
    HEADING_FONT_SIZE_PT,
    HEADING_STYLE_NAME,
    OPENCC_DEFAULT,
    PAGE_MARGIN_CM,
)
from src.review_schema import (
    ParagraphMergeCandidate,
    ReviewCandidate,
    ReviewSchema,
    TocState,
    make_chapter_candidate_id,
    make_review_candidate_id,
    validate_review_schema,
)


def test_frozen_spec_minimum_constants() -> None:
    assert OPENCC_DEFAULT == "s2t"
    assert HEADING_STYLE_NAME == "Heading 2"
    assert FONT_NAME == "\u65b0\u7d30\u660e\u9ad4"
    assert HEADING_FONT_SIZE_PT == 16.0
    assert BODY_FONT_SIZE_PT == 12.0
    assert BODY_FIRST_LINE_INDENT_PT == 24.0
    assert PAGE_MARGIN_CM == 1.27


def test_schema_shape_exists() -> None:
    schema = ReviewSchema()
    assert schema.chapter_candidates == []
    assert schema.review_candidates == []
    assert schema.paragraph_merge_candidates == []
    assert schema.toc.requested is False
    assert schema.toc.status == "not_requested"
    assert schema.warnings == []
    assert schema.errors == []
    validate_review_schema(schema)


def test_toc_state_default_is_semantically_consistent() -> None:
    toc = TocState()
    assert toc.requested is False
    assert toc.status == "not_requested"
    assert toc.fallback_used is False
    assert toc.chapter_count == 0


def test_candidate_id_is_stable() -> None:
    first = make_chapter_candidate_id(12, "chapter_rule", "\u7b2c\u5341\u7ae0")
    second = make_chapter_candidate_id(12, "chapter_rule", "\u7b2c\u5341\u7ae0")
    assert first == second
    assert first.startswith("chapter:12:chapter_rule:")

    risk_id = make_review_candidate_id("risk_rule", 7, 3, "\u7684")
    assert risk_id.startswith("risk:risk_rule:7:3:")


def test_review_candidates_do_not_allow_auto_accepted() -> None:
    schema = ReviewSchema(
        review_candidates=[
            ReviewCandidate(
                candidate_id="risk:r:1:1:abcdef123456",
                status="auto_accepted",
            )
        ]
    )
    with pytest.raises(ValueError, match="auto_accepted"):
        validate_review_schema(schema)


def test_paragraph_merge_auto_apply_must_be_false() -> None:
    schema = ReviewSchema(
        paragraph_merge_candidates=[
            ParagraphMergeCandidate(
                candidate_id="paragraph_merge:1:2:abcdef123456",
                auto_apply=True,
            )
        ]
    )
    with pytest.raises(ValueError, match="auto_apply"):
        validate_review_schema(schema)
