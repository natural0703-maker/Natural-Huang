from src.converter import OpenCCConverter


def test_opencc_basic_conversion() -> None:
    converter = OpenCCConverter("s2twp.json")
    assert converter.convert("后") == "後"

