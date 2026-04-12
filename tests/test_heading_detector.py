from src.heading_detector import is_direct_chapter_heading


def test_direct_heading_patterns() -> None:
    assert is_direct_chapter_heading("第一章")
    assert is_direct_chapter_heading("第一章 我見猶憐")
    assert is_direct_chapter_heading("第一章：我見猶憐")
    assert is_direct_chapter_heading("第12章 意外重逢")
    assert is_direct_chapter_heading("第3回 山雨欲來")
    assert is_direct_chapter_heading("第2節：再會")


def test_heading_whitelist() -> None:
    assert is_direct_chapter_heading("序章")
    assert is_direct_chapter_heading("楔子")
    assert is_direct_chapter_heading("終章")
    assert is_direct_chapter_heading("後記")
    assert is_direct_chapter_heading("番外")
    assert is_direct_chapter_heading("尾聲")


def test_normal_short_sentence_not_heading() -> None:
    assert not is_direct_chapter_heading("今天下雨了")
    assert not is_direct_chapter_heading("我見猶憐")
    assert not is_direct_chapter_heading("重要提醒")
