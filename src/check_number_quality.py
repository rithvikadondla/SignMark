from pathlib import Path
import cv2
import hashlib
import json
from collections import Counter, defaultdict

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data" / "processed"
REPORT_DIR = ROOT / "reports"

SPLITS = ["train", "test"]
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}

report = {
    "class_counts": {},
    "corrupted_images": {},
    "duplicate_groups": {},
    "cross_split_duplicates": [],
    "image_dimensions": {},
    "missing_classes": {},
}

hashes_by_split = {}
all_dimensions = Counter()

for split in SPLITS:
    split_dir = DATA_DIR / split
    split_hashes = defaultdict(list)
    corrupted = []
    dimensions = Counter()
    class_counts = {}

    if not split_dir.exists():
        print(f"Missing folder: {split_dir}")
        continue

    for digit in map(str, range(10)):
        class_dir = split_dir / digit

        if not class_dir.exists():
            class_counts[digit] = 0
            continue

        files = [
            p
            for p in class_dir.iterdir()
            if p.is_file() and p.suffix.lower() in IMAGE_EXTENSIONS
        ]

        class_counts[digit] = len(files)

        for file in files:
            try:
                image = cv2.imread(str(file), cv2.IMREAD_UNCHANGED)

                if image is None or image.size == 0:
                    corrupted.append(str(file.relative_to(ROOT)))
                    continue

                height, width = image.shape[:2]
                channels = 1 if image.ndim == 2 else image.shape[2]

                dimensions[f"{width}x{height}, {channels} channels"] += 1
                all_dimensions[f"{width}x{height}, {channels} channels"] += 1

                digest = hashlib.sha256(file.read_bytes()).hexdigest()
                split_hashes[digest].append(str(file.relative_to(ROOT)))

            except Exception:
                corrupted.append(str(file.relative_to(ROOT)))

    duplicates = {
        digest: paths for digest, paths in split_hashes.items() if len(paths) > 1
    }

    report["class_counts"][split] = class_counts
    report["corrupted_images"][split] = corrupted
    report["duplicate_groups"][split] = len(duplicates)
    report["image_dimensions"][split] = dict(dimensions)
    report["missing_classes"][split] = [
        digit for digit in map(str, range(10)) if class_counts[digit] == 0
    ]

    hashes_by_split[split] = split_hashes

# Check exact duplicate files shared across train and test
if "train" in hashes_by_split and "test" in hashes_by_split:
    common = set(hashes_by_split["train"]) & set(hashes_by_split["test"])

    for digest in common:
        report["cross_split_duplicates"].append(
            {
                "train": hashes_by_split["train"][digest],
                "test": hashes_by_split["test"][digest],
            }
        )

report["all_image_dimensions"] = dict(all_dimensions)

REPORT_DIR.mkdir(parents=True, exist_ok=True)
output = REPORT_DIR / "number_quality_report.json"
output.write_text(json.dumps(report, indent=2), encoding="utf-8")

print("\n========== NUMBER DATASET QUALITY ==========")

for split in SPLITS:
    if split not in report["class_counts"]:
        continue

    print(f"\n{split.upper()}")
    for digit, count in report["class_counts"][split].items():
        print(f"  {digit}: {count}")

    print("Corrupted:", len(report["corrupted_images"][split]))
    print("Duplicate groups:", report["duplicate_groups"][split])
    print("Missing classes:", report["missing_classes"][split])

print("\nCross-split duplicate groups:", len(report["cross_split_duplicates"]))

print("\nImage dimensions:")
for dimension, count in report["all_image_dimensions"].items():
    print(f"  {dimension}: {count}")

print(f"\nFull report saved to: {output}")
