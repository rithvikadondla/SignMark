"""Build cached training arrays for the NUMBER and PHRASE datasets (no pandas).
Run from the project root (after audit_numbers.py and prepare_phrases.py):
    python src/prepare_arrays.py

Output in data/processed/ (uint8 RGB arrays; divide by 255 when training):
    numbers_{train,val,test}_x_<size>.npy / _y.npy   + label_map_numbers.json + numbers_manifest.json
    phrases_{train,val,test}_x_<size>.npy / _y.npy   + label_map_phrases.json + phrases_manifest.json
    arrays_info.json (all settings and counts)

Rules:
- Numbers: ALL images of the existing folders data/processed/train and data/processed/test are
  used (duplicates are accepted, nothing is excluded). Validation is carved from TRAIN only
  (random, stratified per class, seed 42). The original test folder is the test set.
- Phrases: train/test are the folders made by prepare_phrases.py; validation is
  carved from TRAIN only (a few images per class). Test is never used for training.
- Original and processed image files are only read.
- Existing output files are never overwritten. If they exist the script stops, unless you
  run it with --rebuild: then the old numbers_*, phrases_* files, label maps and
  arrays_info.json are MOVED into data/processed/arrays_previous_<time>/ (kept, not deleted).
"""
import argparse
import json
import random
import shutil
import sys
import time
from collections import defaultdict
from pathlib import Path

import cv2
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from audit_utils import PROJECT_ROOT, class_folders, image_files

PROC = PROJECT_ROOT / "data" / "processed"


def load_rgb(path, size):
    """Decode (any channel count -> 3 channels), RGB, resize to size x size."""
    img = cv2.imdecode(np.fromfile(str(path), dtype=np.uint8), cv2.IMREAD_COLOR)
    if img is None:
        raise ValueError("cannot decode")
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    return cv2.resize(img, (size, size), interpolation=cv2.INTER_AREA)


def build_arrays(name, split, items, size, label_map):
    """items: list of (relative_path, class_name). Saves x and y; returns (kept, skipped)."""
    x = np.zeros((len(items), size, size, 3), dtype=np.uint8)
    y, kept, skipped = [], [], []
    k = 0
    for i, (rel, cls) in enumerate(items, 1):
        try:
            x[k] = load_rgb(PROJECT_ROOT / rel, size)
        except Exception as e:
            skipped.append({"path": rel, "error": str(e)})
            continue
        y.append(label_map[cls])
        kept.append(rel)
        k += 1
        if i % 2000 == 0:
            print(f"  {name} {split}: {i}/{len(items)}")
    np.save(PROC / f"{name}_{split}_x_{size}.npy", x[:k])
    np.save(PROC / f"{name}_{split}_y.npy", np.array(y, dtype=np.int64))
    return kept, skipped


def stratified_val(items, val_frac, rng):
    """items: (rel, cls). Hold out ~val_frac of every class for validation."""
    by_class = defaultdict(list)
    for rel, cls in items:
        by_class[cls].append((rel, cls))
    train, val = [], []
    for cls in sorted(by_class):
        files = sorted(by_class[cls])
        rng.shuffle(files)
        n_val = round(len(files) * val_frac)
        val += files[:n_val]
        train += files[n_val:]
    return train, val


def make_numbers(args, info):
    train_dir, test_dir = PROC / "train", PROC / "test"
    if not (train_dir.is_dir() and test_dir.is_dir()):
        sys.exit("Number folders data/processed/train and data/processed/test not found.")
    def listing(root):
        return [(f.relative_to(PROJECT_ROOT).as_posix(), d.name)
                for d in class_folders(root) for f in image_files(d)]
    label_map = {str(d): d for d in range(10)}
    train_all, test = listing(train_dir), listing(test_dir)
    unknown = {c for _, c in train_all + test} - set(label_map)
    if unknown:
        sys.exit(f"Unexpected class folders in the number data: {sorted(unknown)}")
    train, val = stratified_val(train_all, args.val_frac, random.Random(args.seed))
    return "numbers", args.number_size, label_map, {"train": train, "val": val, "test": test}


def make_phrases(args, info):
    root = PROC / "phrases"
    if not (root / "train").is_dir():
        sys.exit("Run python src/prepare_phrases.py first.")
    classes = [d.name for d in class_folders(root / "train")]
    label_map = {c: i for i, c in enumerate(classes)}
    rng = random.Random(args.seed)
    train, val, test = [], [], []
    for c in classes:
        files = [f.relative_to(PROJECT_ROOT).as_posix() for f in image_files(root / "train" / c)]
        rng.shuffle(files)
        val += [(f, c) for f in files[:args.phrase_val_per_class]]
        train += [(f, c) for f in files[args.phrase_val_per_class:]]
        test += [(f.relative_to(PROJECT_ROOT).as_posix(), c) for f in image_files(root / "test" / c)]
    return "phrases", args.phrase_size, label_map, {"train": train, "val": val, "test": test}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--number-size", type=int, default=64)
    parser.add_argument("--phrase-size", type=int, default=128)
    parser.add_argument("--val-frac", type=float, default=0.15, help="numbers validation share of train")
    parser.add_argument("--phrase-val-per-class", type=int, default=4)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--rebuild", action="store_true",
                        help="move existing number/phrase arrays into a backup folder and rebuild")
    args = parser.parse_args()

    if (PROC / "arrays_info.json").exists():
        if not args.rebuild:
            sys.exit("data/processed/arrays_info.json already exists. Nothing was changed. "
                     "Run again with --rebuild to back up the old arrays and rebuild them.")
        backup = PROC / f"arrays_previous_{time.strftime('%Y%m%d_%H%M%S')}"
        backup.mkdir()
        old = [f for pat in ("numbers_*", "phrases_*", "label_map_numbers.json",
                             "label_map_phrases.json", "arrays_info.json")
               for f in PROC.glob(pat) if f.is_file()]
        for f in old:
            shutil.move(str(f), str(backup / f.name))
        print(f"Moved {len(old)} old files to {backup.name}")
    info = {"seed": args.seed, "number_size": args.number_size, "phrase_size": args.phrase_size,
            "dtype": "uint8", "colour": "RGB", "resize": "cv2.INTER_AREA, squashed to a square",
            "normalisation": "divide by 255 at training time"}
    for make in (make_numbers, make_phrases):
        name, size, label_map, splits = make(args, info)
        (PROC / f"label_map_{name}.json").write_text(json.dumps(label_map, indent=2))
        manifest, skipped_all = {}, {}
        info[name] = {"classes": len(label_map)}
        for split, items in splits.items():
            print(f"Building {name} {split} ({len(items)} images)...")
            kept, skipped = build_arrays(name, split, items, size, label_map)
            manifest[split] = kept
            info[name][split] = {"images": len(kept), "skipped": skipped}
        (PROC / f"{name}_manifest.json").write_text(json.dumps(manifest, indent=1))
    (PROC / "arrays_info.json").write_text(json.dumps(info, indent=2))
    print(json.dumps({k: ({s: (v[s]["images"], len(v[s]["skipped"])) for s in ("train", "val", "test")}
                          if isinstance(v, dict) and "train" in v else v)
                      for k, v in info.items() if k in ("numbers", "phrases")}, indent=2))
    print("Format above: split: (images, skipped)")


if __name__ == "__main__":
    main()