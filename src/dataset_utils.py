"""Shared helpers for SignMark dataset scripts."""

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = PROJECT_ROOT / "data" / "raw"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
REPORTS_DIR = PROJECT_ROOT / "reports"
IMAGE_EXTS = {".jpg", ".jpeg", ".png"}


def find_split_dir(split):
    """Find the folder 'asl_alphabet_<split>' (deepest match, since it is nested)."""
    matches = [p for p in RAW_DIR.rglob(f"asl_alphabet_{split}") if p.is_dir()]
    if not matches:
        raise FileNotFoundError(
            f"No 'asl_alphabet_{split}' folder found under {RAW_DIR}"
        )
    return max(matches, key=lambda p: len(p.parts))


def list_class_dirs(train_dir):
    """Return sorted class folders inside the training directory."""
    return sorted(p for p in Path(train_dir).iterdir() if p.is_dir())


def list_images(folder):
    """Return sorted image files directly inside a folder."""
    return sorted(
        p
        for p in Path(folder).iterdir()
        if p.is_file() and p.suffix.lower() in IMAGE_EXTS
    )


def test_label(path):
    """Test files are named like 'A_test.jpg' -> label 'A'."""
    return Path(path).stem.split("_")[0]
