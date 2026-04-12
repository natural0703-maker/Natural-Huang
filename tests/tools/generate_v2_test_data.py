from pathlib import Path

from docx import Document


ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "tests" / "data"
BATCH_DIR = DATA_DIR / "batch_input"
SUB_DIR = BATCH_DIR / "subfolder"


def _write_docx(path: Path, paragraphs: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    doc = Document()
    for text in paragraphs:
        doc.add_paragraph(text)
    doc.save(str(path))


def main() -> int:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    BATCH_DIR.mkdir(parents=True, exist_ok=True)
    SUB_DIR.mkdir(parents=True, exist_ok=True)

    _write_docx(
        DATA_DIR / "single_ok.docx",
        [
            "\u8fd9\u662f \u4e00\u4e2a \u8f6f\u4ef6 \u6587\u6863\u3002",
            "\u9019\u88e1\u7684\u8cc7\u8a0a\u8981\u4eba\u5de5\u8907\u6838\uff0c\u4e0d\u53ef\u76f4\u63a5\u6539\u52d5\u3002",
        ],
    )
    _write_docx(
        BATCH_DIR / "normal_1.docx",
        [
            "\u8fd9\u662f \u670d\u52a1\u5668 \u5c4f\u5e55 \u6d4b\u8bd5\u3002",
            "\u9f20\u6807 \u5728 \u684c\u4e0a\u3002",
        ],
    )
    _write_docx(
        BATCH_DIR / "risk_terms.docx",
        [
            "\u9019\u88e1\u7684\u8cc7\u8a0a\u8207\u652f\u6301\u6d41\u7a0b\u8981\u4eba\u5de5\u5224\u65b7\u3002",
            "\u5f97 \u7684 \u5730 \u4f7f\u7528\u8981\u4eba\u5de5\u8907\u6838\u3002",
        ],
    )
    _write_docx(
        BATCH_DIR / "anomaly.docx",
        [
            "\u9019\u662f?\u7570\u5e38\u5b57\u5143\u6383\u63cf\u6a23\u672c\u3002",
            "\u7b2c\u4e8c\u6bb5\u542b\u6709\u4e0d\u53ef\u898b\u5b57\u5143\u200b\u6e2c\u8a66\u3002",
        ],
    )
    _write_docx(
        SUB_DIR / "sub_test.docx",
        [
            "\u5b50\u8cc7\u6599\u593e\u6e2c\u8a66\u6587\u4ef6\u3002",
            "\u8fd9\u662f \u5b50\u76ee\u5f55 \u6587\u6863\u3002",
        ],
    )

    # 非 docx，應被批次輸入掃描忽略
    (BATCH_DIR / "ignore.txt").write_text("ignore me", encoding="utf-8")

    # 故意建立壞掉的 .docx，應在批次結果中進 failures
    (BATCH_DIR / "bad.docx").write_text("this is not a valid docx zip package", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
