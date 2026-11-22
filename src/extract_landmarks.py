"""Extract normalised MediaPipe hand-landmark features for every split.
Run from the project root:
    python src/extract_landmarks.py --max-per-class 100     (quick test)
    python src/extract_landmarks.py                         (full run, can take a while)

Reads data/processed/{train,val,test}.csv, writes
    data/processed/landmarks_<split>.npz   (X: n x 63, y: label ids, paths)
    reports/landmark_detection_report.json (how often a hand was found, per class)

Class 'nothing' (no hand in the image) is NOT used for training. At prediction time
"no hand detected" is reported by the detector instead.
Images where no hand is detected are left out and counted in the report.
"""

import argparse
import csv
import json
import sys
import time
from collections import defaultdict
from pathlib import Path

import cv2
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from dataset_utils import PROCESSED_DIR, PROJECT_ROOT, REPORTS_DIR
from hand_detection import HandDetector

SKIP_CLASSES = {"nothing"}


def read_manifest(split):
    with open(PROCESSED_DIR / f"{split}.csv", newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def run_split(split, detector, max_per_class):
    rows = [r for r in read_manifest(split) if r["label"] not in SKIP_CLASSES]
    if max_per_class:
        taken, kept = defaultdict(int), []
        for r in rows:
            if taken[r["label"]] < max_per_class:
                kept.append(r)
                taken[r["label"]] += 1
        rows = kept
    X, y, paths = [], [], []
    stats = defaultdict(lambda: {"total": 0, "detected": 0})
    start = time.time()
    for i, r in enumerate(rows, 1):
        stats[r["label"]]["total"] += 1
        img = cv2.imread(str(PROJECT_ROOT / r["path"]))
        if img is None:
            continue
        feats, _ = detector.features(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
        if feats is None:
            continue
        stats[r["label"]]["detected"] += 1
        X.append(feats)
        y.append(int(r["label_id"]))
        paths.append(r["path"])
        if i % 2000 == 0:
            rate = i / (time.time() - start)
            print(f"  {split}: {i}/{len(rows)} ({rate:.1f} img/s)")
    np.savez_compressed(
        PROCESSED_DIR / f"landmarks_{split}.npz",
        X=np.array(X, dtype=np.float32),
        y=np.array(y, dtype=np.int64),
        paths=np.array(paths),
    )
    return {
        "images_tried": len(rows),
        "hands_detected": len(X),
        "per_class": {
            k: dict(v, rate=round(v["detected"] / v["total"], 3))
            for k, v in sorted(stats.items())
        },
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--max-per-class",
        type=int,
        default=0,
        help="limit images per class per split (0 = all)",
    )
    args = parser.parse_args()
    for s in ("train", "val", "test"):
        if not (PROCESSED_DIR / f"{s}.csv").exists():
            sys.exit("Run python src/split_dataset.py first.")
    detector = HandDetector()
    report = {
        "max_per_class": args.max_per_class,
        "skipped_classes": sorted(SKIP_CLASSES),
    }
    for s in ("train", "val", "test"):
        print(f"Extracting {s}...")
        report[s] = run_split(s, detector, args.max_per_class)
        print(
            f"  {s}: {report[s]['hands_detected']}/{report[s]['images_tried']} hands detected"
        )
    detector.close()
    REPORTS_DIR.mkdir(exist_ok=True)
    (REPORTS_DIR / "landmark_detection_report.json").write_text(
        json.dumps(report, indent=2)
    )
    print(
        "Saved reports/landmark_detection_report.json and data/processed/landmarks_*.npz"
    )


if __name__ == "__main__":
    main()
