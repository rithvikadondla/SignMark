"""Create train / validation / test manifests (CSV files). No images are copied.
Run from the project root:  python src/split_dataset.py
Uses only the Python standard library (no pandas, no scikit-learn).

Why we do not use the official test folder: its files are byte-identical to
training images (see reports/dataset_quality_report.json).

How leakage is reduced:
- Every class appears in every split (stratified per class).
- Consecutive file numbers (A1..A100) are kept together in one split, because
  neighbouring frames are nearly identical. Block size is configurable.
- A fixed seed makes the split reproducible.
Limitation: images come from one capture setting, so scores will look better
than real webcam performance.
"""

import argparse
import csv
import json
import random
import re
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from dataset_utils import (
    PROCESSED_DIR,
    PROJECT_ROOT,
    find_split_dir,
    list_class_dirs,
    list_images,
)


def group_id(path, block):
    """Images with nearby file numbers share a group (e.g. A1..A100 -> block 0)."""
    m = re.search(r"(\d+)\.\w+$", path.name)
    if block > 0 and m:
        return int(m.group(1)) // block
    return path.name  # no number: the image is its own group


def split_class(files, block, test_frac, val_frac, rng):
    """Split one class's files into (train, val, test) by whole groups."""
    groups = defaultdict(list)
    for f in files:
        groups[group_id(f, block)].append(f)
    keys = sorted(groups, key=str)
    rng.shuffle(keys)
    n = len(files)
    want_test, want_val = round(n * test_frac), round(n * val_frac)
    train, val, test = [], [], []
    for k in keys:
        if len(test) < want_test:
            test += groups[k]
        elif len(val) < want_val:
            val += groups[k]
        else:
            train += groups[k]
    return train, val, test


def write_csv(path, rows):
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=["path", "label", "label_id"])
        w.writeheader()
        w.writerows(rows)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--test-frac", type=float, default=0.15)
    parser.add_argument("--val-frac", type=float, default=0.15)
    parser.add_argument(
        "--block-size",
        type=int,
        default=100,
        help="consecutive file numbers kept together (0 = off)",
    )
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    class_dirs = list_class_dirs(find_split_dir("train"))
    label_map = {d.name: i for i, d in enumerate(class_dirs)}
    rng = random.Random(args.seed)

    splits = {"train": [], "val": [], "test": []}
    for d in class_dirs:
        tr, va, te = split_class(
            list_images(d), args.block_size, args.test_frac, args.val_frac, rng
        )
        for name, files in (("train", tr), ("val", va), ("test", te)):
            splits[name] += [
                {
                    "path": f.relative_to(PROJECT_ROOT).as_posix(),
                    "label": d.name,
                    "label_id": label_map[d.name],
                }
                for f in files
            ]

    # Leakage check: no file may appear in two splits
    seen = {}
    for name, rows in splits.items():
        for r in rows:
            assert r["path"] not in seen, (
                f"{r['path']} is in {seen[r['path']]} and {name}!"
            )
            seen[r["path"]] = name

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    per_class = {name: {} for name in splits}
    for name, rows in splits.items():
        write_csv(PROCESSED_DIR / f"{name}.csv", rows)
        for r in rows:
            per_class[name][r["label"]] = per_class[name].get(r["label"], 0) + 1
    (PROCESSED_DIR / "label_map.json").write_text(json.dumps(label_map, indent=2))

    info = {
        "seed": args.seed,
        "block_size": args.block_size,
        "test_frac": args.test_frac,
        "val_frac": args.val_frac,
        "num_classes": len(label_map),
        "train_images": len(splits["train"]),
        "val_images": len(splits["val"]),
        "test_images": len(splits["test"]),
        "path_overlap_between_splits": 0,
        "official_test_folder": "NOT used: its files are identical to training files",
        "per_class": per_class,
    }
    (PROCESSED_DIR / "split_info.json").write_text(json.dumps(info, indent=2))
    print(json.dumps({k: v for k, v in info.items() if k != "per_class"}, indent=2))
    print(
        "Smallest class per split (train/val/test):",
        min(per_class["train"].values()),
        min(per_class["val"].values()),
        min(per_class["test"].values()),
    )
    print("Saved train.csv, val.csv, test.csv, label_map.json, split_info.json")


if __name__ == "__main__":
    main()
