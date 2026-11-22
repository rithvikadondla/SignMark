"""Inspect the raw dataset. Read-only: never changes raw images.
Run from the project root:  python src/inspect_dataset.py
"""

import hashlib
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
from dataset_utils import (
    REPORTS_DIR,
    PROJECT_ROOT,
    find_split_dir,
    list_class_dirs,
    list_images,
    test_label,
)


def check_image(path):
    """Return (size, mode, format, md5) or raise if unreadable."""
    data = path.read_bytes()
    with Image.open(path) as im:
        info = (im.size, im.mode, im.format)
        im.verify()  # detects truncated/corrupt files
    return info + (hashlib.md5(data).hexdigest(),)


def scan(files, label_of):
    """Scan files; return stats about them."""
    sizes, modes, formats = Counter(), Counter(), Counter()
    corrupted, hashes = [], defaultdict(list)
    for i, f in enumerate(files, 1):
        try:
            size, mode, fmt, md5 = check_image(f)
        except Exception as e:  # unreadable image
            corrupted.append(
                {"file": str(f.relative_to(PROJECT_ROOT)), "error": str(e)}
            )
            continue
        sizes[f"{size[0]}x{size[1]}"] += 1
        modes[mode] += 1
        formats[fmt] += 1
        hashes[md5].append(str(f.relative_to(PROJECT_ROOT)))
        if i % 10000 == 0:
            print(f"  scanned {i} images...")
    return sizes, modes, formats, corrupted, hashes


def main():
    train_dir, test_dir = find_split_dir("train"), find_split_dir("test")
    print("Train dir:", train_dir)
    print("Test dir :", test_dir)

    class_dirs = list_class_dirs(train_dir)
    classes = [d.name for d in class_dirs]
    train_files, per_class = [], {}
    for d in class_dirs:
        imgs = list_images(d)
        per_class[d.name] = len(imgs)
        train_files += imgs
    test_files = list_images(test_dir)

    print(f"Scanning {len(train_files)} training images (this takes a few minutes)...")
    tr_sizes, tr_modes, tr_fmts, tr_bad, tr_hash = scan(train_files, None)
    print(f"Scanning {len(test_files)} test images...")
    te_sizes, te_modes, te_fmts, te_bad, te_hash = scan(test_files, None)

    dup_groups = {h: p for h, p in tr_hash.items() if len(p) > 1}
    leakage = sorted(set(tr_hash) & set(te_hash))  # identical files in train and test
    test_labels = sorted(test_label(f) for f in test_files)
    counts = list(per_class.values())

    summary = {
        "train_dir": str(train_dir.relative_to(PROJECT_ROOT)),
        "test_dir": str(test_dir.relative_to(PROJECT_ROOT)),
        "num_classes": len(classes),
        "classes": classes,
        "images_per_class": per_class,
        "total_train_images": len(train_files),
        "total_test_images": len(test_files),
        "train_image_sizes": dict(tr_sizes),
        "train_color_modes": dict(tr_modes),
        "train_formats": dict(tr_fmts),
        "test_image_sizes": dict(te_sizes),
        "imbalance_max_over_min": round(max(counts) / min(counts), 3)
        if counts and min(counts)
        else None,
    }
    quality = {
        "empty_classes": [c for c, n in per_class.items() if n == 0],
        "corrupted_train": tr_bad,
        "corrupted_test": te_bad,
        "duplicate_groups_in_train": len(dup_groups),
        "duplicate_images_in_train": sum(len(p) - 1 for p in dup_groups.values()),
        "duplicate_examples": list(dup_groups.values())[:10],
        "identical_files_in_train_and_test": len(leakage),
        "test_labels": test_labels,
        "test_labels_not_in_train": sorted(set(test_labels) - set(classes)),
        "train_classes_without_test_image": sorted(set(classes) - set(test_labels)),
    }

    REPORTS_DIR.mkdir(exist_ok=True)
    (REPORTS_DIR / "dataset_summary.json").write_text(json.dumps(summary, indent=2))
    (REPORTS_DIR / "dataset_quality_report.json").write_text(
        json.dumps(quality, indent=2)
    )
    print(json.dumps(summary, indent=2))
    print(
        json.dumps(
            {k: v for k, v in quality.items() if k != "duplicate_examples"}, indent=2
        )
    )
    print("Saved reports/dataset_summary.json and reports/dataset_quality_report.json")


if __name__ == "__main__":
    main()
