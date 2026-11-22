"""Audit the PHRASE dataset and create an 80/20 per-class train/test split.
Run from the project root:  python src/prepare_phrases.py
(optional)  python src/prepare_phrases.py --raw "data/raw/phrases"

Raw images are only read, never changed. The split is COPIED to
    data/processed/phrases/train/<class>/   and   data/processed/phrases/test/<class>/
If those folders already exist they are renamed to phrases_previous_<time> first
(nothing is deleted or overwritten).

Split rule (stratified, duplicate-aware): inside every class, images with identical
content are kept together, so a copy can never be in train while another copy is in test.
Whole groups are chosen with random.Random(42) so that exactly 8 images per class go to
test and the rest (32) to train.

Writes reports/phrase_quality_report.json and reports/phrase_split_info.json.
"""

import argparse
import random
import shutil
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from audit_utils import (
    PROJECT_ROOT,
    audit_folder,
    class_folders,
    duplicate_groups,
    fingerprint,
    image_files,
    md5_of,
    show_existing_reports,
    write_report,
)

RAW_CANDIDATES = [
    PROJECT_ROOT / "data" / "raw" / "phrases",
    PROJECT_ROOT / "data" / "raw" / "images for phrases",
]
OUT = PROJECT_ROOT / "data" / "processed" / "phrases"


def pick_test_groups(groups, n_test, rng):
    """Choose whole groups whose sizes add up to exactly n_test (randomised)."""
    order = list(range(len(groups)))
    rng.shuffle(order)
    sizes = [len(groups[i]) for i in order]
    suffix = [set() for _ in range(len(order) + 1)]
    suffix[len(order)] = {0}
    for i in range(len(order) - 1, -1, -1):
        suffix[i] = suffix[i + 1] | {s + sizes[i] for s in suffix[i + 1]}
    if n_test not in suffix[0]:
        raise ValueError(
            f"cannot form exactly {n_test} test images from groups of sizes {sorted(sizes)}"
        )
    chosen, cur = [], 0
    for i, size in enumerate(sizes):
        if cur == n_test:
            break
        if cur + size <= n_test and (n_test - cur - size) in suffix[i + 1]:
            chosen.append(order[i])
            cur += size
    return set(chosen)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--raw", default=None, help="raw phrase folder (default: data/raw/phrases)"
    )
    parser.add_argument("--classes", type=int, default=44)
    parser.add_argument("--per-class", type=int, default=40)
    parser.add_argument("--test-per-class", type=int, default=8)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    raw = (
        Path(args.raw)
        if args.raw
        else next((p for p in RAW_CANDIDATES if p.is_dir()), None)
    )
    if raw is None or not raw.is_dir():
        sys.exit('Raw phrase folder not found. Use --raw "path".')
    raw = raw if raw.is_absolute() else PROJECT_ROOT / raw
    print("Using raw folder:", raw.relative_to(PROJECT_ROOT).as_posix())
    show_existing_reports()

    if OUT.exists() and any(OUT.rglob("*.*")):
        backup = OUT.with_name(f"phrases_previous_{time.strftime('%Y%m%d_%H%M%S')}")
        OUT.rename(backup)
        print("Existing processed phrase split kept as", backup.name)

    raw_before = fingerprint(raw)
    print("Auditing raw phrase images...")
    audit = audit_folder(raw)
    n_classes = len(audit["per_class"])
    bad_counts = {c: n for c, n in audit["per_class"].items() if n != args.per_class}
    problems = []
    if n_classes != args.classes:
        problems.append(f"found {n_classes} classes, expected {args.classes}")
    if bad_counts:
        problems.append(
            f"classes without exactly {args.per_class} images: {bad_counts}"
        )
    if audit["corrupted"]:
        problems.append(f"{len(audit['corrupted'])} corrupted images")

    # Duplicate analysis: inside a class (handled by the split) and across classes (a label conflict)
    hash_classes = defaultdict(set)
    for h, paths in audit["hashes"].items():
        for p in paths:
            hash_classes[h].add(Path(p).parent.name)
    cross_class = {h: sorted(c) for h, c in hash_classes.items() if len(c) > 1}
    dups = duplicate_groups(audit["hashes"])

    quality = {
        "dataset": "phrases (static images)",
        "raw_folder": raw.relative_to(PROJECT_ROOT).as_posix(),
        "classes_found": n_classes,
        "expected_classes": args.classes,
        "class_names": sorted(audit["per_class"]),
        "images_per_class": audit["per_class"],
        "total_images": audit["total_images"],
        "classes_with_unexpected_count": bad_counts,
        "image_sizes": audit["image_sizes"],
        "color_modes": audit["color_modes"],
        "channels": audit["channels"],
        "formats": audit["formats"],
        "corrupted_images": audit["corrupted"],
        "duplicate_groups": len(dups),
        "duplicate_files": sum(len(g) - 1 for g in dups),
        "duplicate_examples": dups[:10],
        "identical_images_in_more_than_one_class": len(cross_class),
        "cross_class_examples": [
            {"classes": c} for c in list(cross_class.values())[:10]
        ],
        "problems_found": problems,
        "raw_fingerprint_before": raw_before,
    }
    if problems:
        quality["raw_unchanged"] = raw_before == fingerprint(raw)
        write_report("phrase_quality_report.json", quality)
        sys.exit("STOPPED, split not created: " + "; ".join(problems))

    rng = random.Random(args.seed)
    split = {"train": {}, "test": {}}
    kept_together = 0
    for folder in class_folders(raw):
        by_hash = defaultdict(list)
        for f in image_files(folder):
            by_hash[md5_of(f)].append(f)
        groups = sorted(by_hash.values(), key=lambda g: g[0].name)
        pick = pick_test_groups(groups, args.test_per_class, rng)
        split["test"][folder.name] = [
            f for i, g in enumerate(groups) if i in pick for f in g
        ]
        split["train"][folder.name] = [
            f for i, g in enumerate(groups) if i not in pick for f in g
        ]
        kept_together += sum(1 for i, g in enumerate(groups) if len(g) > 1)

    for part in ("train", "test"):
        for cls, files in split[part].items():
            dest = OUT / part / cls
            dest.mkdir(parents=True, exist_ok=True)
            for f in files:
                shutil.copy2(f, dest / f.name)

    # Verification
    train_names = {(c, f.name) for c, fs in split["train"].items() for f in fs}
    test_names = {(c, f.name) for c, fs in split["test"].items() for f in fs}
    tr_hash = {md5_of(p) for p in (OUT / "train").rglob("*") if p.is_file()}
    te_hash = {md5_of(p) for p in (OUT / "test").rglob("*") if p.is_file()}
    out_train, out_test = audit_folder(OUT / "train"), audit_folder(OUT / "test")
    want_train = args.per_class - args.test_per_class
    ok_counts = (
        all(n == want_train for n in out_train["per_class"].values())
        and all(n == args.test_per_class for n in out_test["per_class"].values())
        and len(out_train["per_class"]) == len(out_test["per_class"]) == args.classes
    )
    raw_after = fingerprint(raw)
    quality.update(
        {"raw_fingerprint_after": raw_after, "raw_unchanged": raw_before == raw_after}
    )
    unique_test = sum(len({md5_of(f) for f in fs}) for fs in split["test"].values())
    unique_train = sum(len({md5_of(f) for f in fs}) for fs in split["train"].values())
    info = {
        "seed": args.seed,
        "raw_folder": quality["raw_folder"],
        "method": "per-class stratified; identical-content copies kept in the same split",
        "classes": n_classes,
        "train_images": out_train["total_images"],
        "test_images": out_test["total_images"],
        "unique_train_images": unique_train,
        "unique_test_images": unique_test,
        "duplicate_groups_kept_together": kept_together,
        "train_per_class": out_train["per_class"],
        "test_per_class": out_test["per_class"],
        "counts_exactly_as_required": ok_counts,
        "file_name_overlap_train_test": len(train_names & test_names),
        "identical_content_overlap_train_test": len(tr_hash & te_hash),
        "identical_images_in_more_than_one_class": len(cross_class),
        "corrupted_in_output": out_train["corrupted"] + out_test["corrupted"],
        "output_folders": [
            "data/processed/phrases/train",
            "data/processed/phrases/test",
        ],
        "test_files": {
            c: sorted(f.name for f in fs) for c, fs in split["test"].items()
        },
        "raw_unchanged": raw_before == raw_after,
    }
    write_report("phrase_quality_report.json", quality)
    write_report("phrase_split_info.json", info)
    print(
        {
            k: info[k]
            for k in (
                "train_images",
                "test_images",
                "unique_train_images",
                "unique_test_images",
                "counts_exactly_as_required",
                "file_name_overlap_train_test",
                "identical_content_overlap_train_test",
                "identical_images_in_more_than_one_class",
                "raw_unchanged",
            )
        }
    )
    print(
        "Quality: sizes",
        quality["image_sizes"],
        "| modes",
        quality["color_modes"],
        "| formats",
        quality["formats"],
        "| duplicate files",
        quality["duplicate_files"],
    )


if __name__ == "__main__":
    main()
