from src.line_break_cleanup import (
    LINE_BREAK_JOINED,
    LINE_BREAK_SKIPPED_BLANK_LINE,
    LINE_BREAK_SKIPPED_LIST_LIKE,
    LINE_BREAK_SKIPPED_SENTENCE_END,
    LINE_BREAK_SKIPPED_SHORT_LINES,
    LINE_BREAK_SKIPPED_UNSAFE_BOUNDARY,
    cleanup_inline_line_breaks,
)


def test_joins_obvious_cjk_line_break() -> None:
    result = cleanup_inline_line_breaks("可現\n在有哪個男生")

    assert result.text == "可現在有哪個男生"
    assert result.applied_count == 1
    assert result.skipped_count == 0
    assert result.codes == {LINE_BREAK_JOINED: 1}


def test_joins_split_person_name() -> None:
    result = cleanup_inline_line_breaks("讓劉\n斌爲之癡迷")

    assert result.text == "讓劉斌爲之癡迷"
    assert result.applied_count == 1


def test_joins_typical_multi_line_case() -> None:
    text = (
        "成績雖算不上十分優秀，可現\n"
        "在有哪個男生找女友是在意女生的成績好壞？容貌與身材的無可挑剔，纔是讓劉\n"
        "斌爲之癡迷的原因。"
    )

    result = cleanup_inline_line_breaks(text)

    assert result.text == (
        "成績雖算不上十分優秀，可現在有哪個男生找女友是在意女生的成績好壞？"
        "容貌與身材的無可挑剔，纔是讓劉斌爲之癡迷的原因。"
    )
    assert result.applied_count == 2
    assert result.skipped_count == 0


def test_joins_after_comma_without_adding_space() -> None:
    result = cleanup_inline_line_breaks("她停了一下，\n然後繼續說")

    assert result.text == "她停了一下，然後繼續說"
    assert result.applied_count == 1


def test_skips_after_sentence_end_punctuation() -> None:
    result = cleanup_inline_line_breaks("他停了下來。\n她沒有回答。")

    assert result.text == "他停了下來。\n她沒有回答。"
    assert result.applied_count == 0
    assert result.skipped_count == 1
    assert result.codes == {LINE_BREAK_SKIPPED_SENTENCE_END: 1}


def test_skips_dialogue_lines() -> None:
    result = cleanup_inline_line_breaks("「你來了？」\n「嗯。」")

    assert result.text == "「你來了？」\n「嗯。」"
    assert result.applied_count == 0
    assert result.codes == {LINE_BREAK_SKIPPED_SENTENCE_END: 1}


def test_skips_list_like_lines() -> None:
    result = cleanup_inline_line_breaks("一、第一項\n二、第二項")

    assert result.text == "一、第一項\n二、第二項"
    assert result.applied_count == 0
    assert result.codes == {LINE_BREAK_SKIPPED_LIST_LIKE: 1}


def test_skips_short_poem_like_lines() -> None:
    result = cleanup_inline_line_breaks("春眠不覺曉\n處處聞啼鳥")

    assert result.text == "春眠不覺曉\n處處聞啼鳥"
    assert result.applied_count == 0
    assert result.codes == {LINE_BREAK_SKIPPED_SHORT_LINES: 1}


def test_skips_english_without_space_inference() -> None:
    result = cleanup_inline_line_breaks("This is a\ntest.")

    assert result.text == "This is a\ntest."
    assert result.applied_count == 0
    assert result.codes == {LINE_BREAK_SKIPPED_UNSAFE_BOUNDARY: 1}


def test_skips_blank_line_boundaries() -> None:
    result = cleanup_inline_line_breaks("第一段\n\n第二段")

    assert result.text == "第一段\n\n第二段"
    assert result.applied_count == 0
    assert result.skipped_count == 2
    assert result.codes == {LINE_BREAK_SKIPPED_BLANK_LINE: 2}


def test_skips_colon_boundary_as_unsafe() -> None:
    result = cleanup_inline_line_breaks("以下內容：\n第一項")

    assert result.text == "以下內容：\n第一項"
    assert result.applied_count == 0
    assert result.codes == {LINE_BREAK_SKIPPED_UNSAFE_BOUNDARY: 1}


def test_text_without_line_break_returns_empty_summary() -> None:
    result = cleanup_inline_line_breaks("沒有斷行的文字")

    assert result.text == "沒有斷行的文字"
    assert result.applied_count == 0
    assert result.skipped_count == 0
    assert result.codes == {}
