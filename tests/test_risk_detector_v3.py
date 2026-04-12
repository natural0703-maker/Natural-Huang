from src.risk_detector import detect_high_risk_terms


def test_risk_category_mapping_v33_and_candidate_id_unique() -> None:
    text = "他的信息在裡面，請支持這個優化。"
    rows = detect_high_risk_terms(
        text=text,
        paragraph_index=3,
        file_name="sample.docx",
        chapter_guess="第一章 測試",
    )

    assert len(rows) >= 4
    by_term = {item.hit_term: item for item in rows}

    assert by_term["信息"].risk_category == "wording"
    assert by_term["裡"].risk_category == "regional_usage"
    assert by_term["支持"].risk_category == "wording"
    assert by_term["優化"].risk_category == "wording"

    ids = [item.candidate_id for item in rows]
    assert len(ids) == len(set(ids))
    assert all(item.chapter_guess == "第一章 測試" for item in rows)
    assert all(item.position_hint for item in rows)
