from src.risk_detector import detect_high_risk_terms


def test_detect_high_risk_terms_basic() -> None:
    text = "這裡的資訊需要人工判斷，請支持這個流程。"
    results = detect_high_risk_terms(
        text=text,
        paragraph_index=2,
        file_name="demo.docx",
    )

    hit_terms = [item.hit_term for item in results]
    assert "裡" in hit_terms
    assert "的" in hit_terms
    assert "資訊" in hit_terms
    assert "支持" in hit_terms
    assert all(item.file_name == "demo.docx" for item in results)
