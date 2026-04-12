from src.gui.main_window_clean import normalize_path_for_display, should_autofill_output_dir


def test_normalize_path_for_display_uses_windows_separator() -> None:
    raw = "C:/Codex Backup/sample.docx"
    normalized = normalize_path_for_display(raw)
    assert "/" not in normalized
    assert "\\" in normalized


def test_autofill_when_output_empty() -> None:
    assert should_autofill_output_dir("", None, False) is True


def test_autofill_keeps_user_manual_output() -> None:
    current = r"D:\Output"
    last_auto = r"C:\Codex Backup"
    assert should_autofill_output_dir(current, last_auto, True) is False


def test_autofill_updates_when_previous_value_is_auto() -> None:
    current = r"C:/Codex Backup"
    last_auto = r"C:\Codex Backup"
    assert should_autofill_output_dir(current, last_auto, False) is True
