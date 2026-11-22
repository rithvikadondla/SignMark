"""Copy one real example photo per sign from YOUR dataset into static/signs/ (used by the dictionary,
text-to-sign and the homepage dividers). Run from the project root:  python src/make_sign_assets.py
Files are named after the sign: A.jpg ... Z.jpg, 0.jpg ... 9.jpg, good_morning.jpg and so on.
Existing files are never overwritten (use --force to replace them). Originals are only read.
These are photos from the datasets you downloaded: check each dataset's licence before publishing the site."""
import argparse
import re
import sys
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "static" / "signs"
EXT = {".jpg", ".jpeg", ".png"}


def middle_image(folder):
    files = sorted(p for p in folder.iterdir() if p.is_file() and p.suffix.lower() in EXT) if folder.is_dir() else []
    return files[len(files) // 2] if files else None


def save(src, label, max_side, force):
    name = re.sub(r"\s+", "_", label.lower() if len(label) > 1 else label) + ".jpg"
    target = OUT / name
    if target.exists() and not force:
        return "kept"
    img = cv2.imdecode(np.fromfile(str(src), dtype=np.uint8), cv2.IMREAD_COLOR)
    if img is None:
        return "unreadable"
    h, w = img.shape[:2]
    scale = min(1.0, max_side / max(h, w))
    if scale < 1:
        img = cv2.resize(img, (round(w * scale), round(h * scale)), interpolation=cv2.INTER_AREA)
    ok, buf = cv2.imencode(".jpg", img, [cv2.IMWRITE_JPEG_QUALITY, 88])
    target.write_bytes(buf.tobytes())
    return "saved"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--size", type=int, default=480, help="longest side of the saved image in pixels")
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    sources = []
    alpha = ROOT / "data/raw/asl_alphabet_train/asl_alphabet_train"
    sources += [(c, middle_image(alpha / c)) for c in "ABCDEFGHIJKLMNOPQRSTUVWXYZ"]
    sources += [(str(d), middle_image(ROOT / f"data/processed/train/{d}")) for d in range(10)]
    pdir = ROOT / "data/processed/phrases/train"
    if pdir.is_dir():
        sources += [(c.name, middle_image(c)) for c in sorted(pdir.iterdir()) if c.is_dir()]
    counts, missing = {"saved": 0, "kept": 0, "unreadable": 0}, []
    for label, src in sources:
        if src is None:
            missing.append(label)
            continue
        counts[save(src, label, args.size, args.force)] += 1
    print(counts, "| signs with no source image:", missing or "none")
    print("Files are in static/signs/. Signs beyond the trained classes still need images from a verified source.")


if __name__ == "__main__":
    main()
