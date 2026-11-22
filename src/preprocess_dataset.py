"""Resize images once and cache them as .npy (uint8) so training is fast.
Run from the project root:  python src/preprocess_dataset.py --size 64
Needs the CSV files made by src/split_dataset.py. No pandas required.

Pixels are saved as uint8 (0-255). Divide by 255 when training (same function
for inference). Raw images are never modified. Unreadable images are skipped.
"""

import argparse
import csv
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
from dataset_utils import PROCESSED_DIR, PROJECT_ROOT


def load_and_resize(path, size):
    """Open an image, convert to RGB, resize to size x size. Same code used at inference."""
    with Image.open(path) as im:
        return np.asarray(
            im.convert("RGB").resize((size, size), Image.BILINEAR), dtype=np.uint8
        )


def read_manifest(name):
    with open(PROCESSED_DIR / f"{name}.csv", newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def process_split(name, size):
    rows = read_manifest(name)
    out_x = PROCESSED_DIR / f"{name}_x_{size}.npy"
    mem = np.lib.format.open_memmap(
        out_x, mode="w+", dtype=np.uint8, shape=(len(rows), size, size, 3)
    )
    labels, skipped = [], []
    k = 0
    for i, row in enumerate(rows):
        try:
            mem[k] = load_and_resize(PROJECT_ROOT / row["path"], size)
            labels.append(int(row["label_id"]))
            k += 1
        except Exception as e:
            skipped.append({"path": row["path"], "error": str(e)})
        if (i + 1) % 10000 == 0:
            print(f"  {name}: {i + 1}/{len(rows)}")
    mem.flush()
    del mem
    if skipped:  # drop unused rows at the end of the array
        arr = np.load(out_x, mmap_mode="r")[:k].copy()
        np.save(out_x, arr)
    np.save(PROCESSED_DIR / f"{name}_y.npy", np.array(labels, dtype=np.int64))
    return {"images": k, "skipped": skipped}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--size", type=int, default=64, help="output width and height")
    args = parser.parse_args()
    for name in ("train", "val", "test"):
        if not (PROCESSED_DIR / f"{name}.csv").exists():
            sys.exit("Run python src/split_dataset.py first.")
    report = {
        "image_size": args.size,
        "interpolation": "bilinear",
        "dtype": "uint8",
        "normalisation": "divide by 255 at training time",
    }
    for name in ("train", "val", "test"):
        print(f"Processing {name}...")
        report[name] = process_split(name, args.size)
    (PROCESSED_DIR / "preprocess_info.json").write_text(json.dumps(report, indent=2))
    print(
        json.dumps(
            {
                k: (
                    v
                    if not isinstance(v, dict)
                    else {"images": v["images"], "skipped": len(v["skipped"])}
                )
                for k, v in report.items()
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
