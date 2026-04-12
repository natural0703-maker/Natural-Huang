from src.anomaly_detector import detect_anomalies


def test_detect_anomalies_basic() -> None:
    original = "這是?原文"
    converted = "這是?轉換後\u200b內容"
    records = detect_anomalies(
        original_text=original,
        converted_text=converted,
        paragraph_index=1,
        file_name="sample.docx",
    )

    chars = [item.anomaly_char for item in records]
    assert "?" in chars
    assert "\u200b" in chars
    assert all(item.file_name == "sample.docx" for item in records)

