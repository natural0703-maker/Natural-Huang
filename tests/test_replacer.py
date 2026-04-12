from src.replacer import apply_replacements


def test_replacer_longest_match_and_count() -> None:
    term_mapping = {
        "伺服器": "服務器",
        "服器": "錯誤替換",
    }
    text = "伺服器與伺服器"

    replaced, records, total = apply_replacements(
        text=text,
        paragraph_index=1,
        term_mapping=term_mapping,
    )

    assert replaced == "服務器與服務器"
    assert total == 2
    assert len(records) == 1
    assert records[0].replaced_term == "伺服器"
    assert records[0].replacement_count == 2

