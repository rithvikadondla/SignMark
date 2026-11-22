"""Shared helpers for the number and phrase dataset audits (no pandas).
Everything here only READS image files; nothing in the raw data is modified."""

import hashlib
import json
import time
from collections import Counter, defaultdict
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

PROJECT_ROOT = Path(__file__).resolve().parents[1]
REPORTS_DIR = PROJECT_ROOT / "reports"
IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".bmp"}


def class_folders(root):
    """Sorted sub-folders of root (one per class)."""
    return sorted(p for p in Path(root).iterdir() if p.is_dir())


def image_files(folder):
    return sorted(
        p
        for p in Path(folder).iterdir()
        if p.is_file() and p.suffix.lower() in IMAGE_EXTS
    )


def md5_of(path):
    return hashlib.md5(Path(path).read_bytes()).hexdigest()


def inspect_image(path):
    """Return dict(width, height, mode, format, channels). Raises if unreadable."""
    with Image.open(path) as im:
        info = {
            "width": im.size[0],
            "height": im.size[1],
            "mode": im.mode,
            "format": im.format,
        }
        im.verify()
    img = cv2.imdecode(np.fromfile(str(path), dtype=np.uint8), cv2.IMREAD_UNCHANGED)
    if img is None:
        raise ValueError("OpenCV could not decode the image")
    info["channels"] = 1 if img.ndim == 2 else int(img.shape[2])
    return info


def audit_folder(root):
    """Audit every class folder under root. Returns a dict of plain statistics."""
    per_class, sizes, modes, formats, channels = (
        {},
        Counter(),
        Counter(),
        Counter(),
        Counter(),
    )
    corrupted, hashes = [], defaultdict(list)
    for folder in class_folders(root):
        files = image_files(folder)
        per_class[folder.name] = len(files)
        for f in files:
            rel = f.relative_to(PROJECT_ROOT).as_posix()
            try:
                info = inspect_image(f)
            except Exception as e:
                corrupted.append({"file": rel, "error": str(e)})
                continue
            sizes[f"{info['width']}x{info['height']}"] += 1
            modes[info["mode"]] += 1
            formats[info["format"]] += 1
            channels[str(info["channels"])] += 1
            hashes[md5_of(f)].append(rel)
    return {
        "per_class": per_class,
        "total_images": sum(per_class.values()),
        "image_sizes": dict(sizes),
        "color_modes": dict(modes),
        "formats": dict(formats),
        "channels": dict(channels),
        "corrupted": corrupted,
        "hashes": dict(hashes),
    }


def duplicate_groups(hashes):
    """Groups of identical files inside one folder tree."""
    return [paths for paths in hashes.values() if len(paths) > 1]


def fingerprint(root):
    """(file count, sha256 of sorted 'path:size:mtime_ns') to detect any later change."""
    h, n = hashlib.sha256(), 0
    for p in sorted(Path(root).rglob("*")):
        if p.is_file():
            st = p.stat()
            h.update(
                f"{p.relative_to(root).as_posix()}:{st.st_size}:{st.st_mtime_ns}".encode()
            )
            n += 1
    return {"files": n, "sha256": h.hexdigest()}


def show_existing_reports():
    """Print which report files already exist, so nothing is overwritten unseen."""
    REPORTS_DIR.mkdir(exist_ok=True)
    found = sorted(p.name for p in REPORTS_DIR.glob("*.json"))
    print("Existing JSON reports in reports/:", found if found else "none")
    return found


def write_report(name, data):
    """Write reports/<name>. An existing file is renamed (kept), never overwritten."""
    REPORTS_DIR.mkdir(exist_ok=True)
    target = REPORTS_DIR / name
    if target.exists():
        backup = target.with_name(
            f"{target.stem}.previous_{time.strftime('%Y%m%d_%H%M%S')}.json"
        )
        target.rename(backup)
        print(f"Existing {name} kept as {backup.name}")
    target.write_text(json.dumps(data, indent=2), encoding="utf-8")
    print(f"Saved reports/{name}")
