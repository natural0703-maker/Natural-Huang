from pathlib import Path
from uuid import uuid4


def make_test_dir(name: str) -> Path:
    root = Path(__file__).resolve().parent / ".test_work"
    path = root / f"{name}_{uuid4().hex}"
    path.mkdir(parents=True, exist_ok=True)
    return path
