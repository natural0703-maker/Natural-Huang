from opencc import OpenCC


class OpenCCConverter:
    def __init__(self, config_name: str) -> None:
        normalized = config_name.strip()
        if normalized.endswith(".json"):
            normalized = normalized[:-5]
        self._converter = OpenCC(normalized)

    def convert(self, text: str) -> str:
        return self._converter.convert(text)
