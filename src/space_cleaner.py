import regex


CHINESE_PUNCTUATION = (
    "\uFF0C\u3002\uFF01\uFF1F\uFF1B\uFF1A\u3001"
    "\uFF08\uFF09\u300A\u300B\u300C\u300D\u300E\u300F"
    "\u3010\u3011\u3014\u3015\u2026\u2014"
)


def clean_text_spacing(text: str) -> str:
    cleaned = text.strip()

    cleaned = regex.sub(r"([\p{Han}]) +(?=[\p{Han}])", r"\1", cleaned)
    cleaned = regex.sub(
        rf"([\p{{Han}}]) +(?=[{regex.escape(CHINESE_PUNCTUATION)}])",
        r"\1",
        cleaned,
    )
    cleaned = regex.sub(
        rf"([{regex.escape(CHINESE_PUNCTUATION)}]) +(?=[\p{{Han}}])",
        r"\1",
        cleaned,
    )

    return cleaned
