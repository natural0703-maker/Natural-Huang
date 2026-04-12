from src.replacer import apply_replacements, filter_out_high_risk_terms
from src.risk_detector import detect_high_risk_terms
from src.risk_terms import HIGH_RISK_TERMS


class DummyConverter:
    def convert(self, text: str) -> str:
        return text.replace("信息", "資訊")


def test_high_risk_terms_appear_in_review_candidates() -> None:
    text = "這裡的資訊支持人工複核。"
    candidates = detect_high_risk_terms(
        text=text,
        paragraph_index=1,
        file_name="demo.docx",
    )
    hit_terms = [item.hit_term for item in candidates]
    assert "裡" in hit_terms
    assert "的" in hit_terms
    assert "資訊" in hit_terms
    assert "支持" in hit_terms


def test_high_risk_terms_are_not_modified_by_low_risk_replacer() -> None:
    converter = DummyConverter()
    raw_mapping = {
        "支持": "支援",
        "資訊": "訊息",
        "軟件": "軟體",
        "信息": "消息",
    }
    filtered_mapping = filter_out_high_risk_terms(
        term_mapping=raw_mapping,
        high_risk_terms=HIGH_RISK_TERMS,
        converter=converter,
    )

    text = "支持 資訊 軟件 信息"
    replaced_text, _, _ = apply_replacements(
        text=text,
        paragraph_index=1,
        term_mapping=filtered_mapping,
        file_name="demo.docx",
    )

    assert replaced_text == "支持 資訊 軟體 信息"
