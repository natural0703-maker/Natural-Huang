from src.space_cleaner import clean_text_spacing


def test_space_cleaner_rules() -> None:
    text = "  這 是 測試 ， 內容 abc def  "
    cleaned = clean_text_spacing(text)
    assert cleaned == "這是測試，內容 abc def"

