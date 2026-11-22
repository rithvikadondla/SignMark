"""Audit the existing NUMBER dataset (read-only). Keeps the train/test split as it is.
Run from the project root:  python src/audit_numbers.py
Expects data/processed/train/<digit>/ and data/processed/test/<digit>/.

Writes reports/number_quality_report.json and data/processed/number_clean_manifest.json
(a list of files; no images are copied, moved or deleted).
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from audit_utils import (
    PROJECT_ROOT,
    audit_folder,
    duplicate_groups,
    fingerprint,
    show_existing_reports,
    write_report,
)

TRAIN = PROJECT_ROOT / "data" / "processed" / "train"
TEST = PROJECT_ROOT / "data" / "processed" / "test"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--expected-train-per-class", type=int, default=800)
    parser.add_argument("--expected-test-per-class", type=int, default=200)
    args = parser.parse_args()

    show_existing_reports()
    for p in (TRAIN, TEST):
        if not p.is_dir():
            sys.exit(f"Folder not found: {p}")
    fp_before = {"train": fingerprint(TRAIN), "test": fingerprint(TEST)}
    print("Auditing train...")
    tr = audit_folder(TRAIN)
    print("Auditing test...")
    te = audit_folder(TEST)

    expected = [str(d) for d in range(10)]
    missing_train = [c for c in expected if c not in tr["per_class"]]
    missing_test = [c for c in expected if c not in te["per_class"]]
    extra = sorted((set(tr["per_class"]) | set(te["per_class"])) - set(expected))
    wrong_train = {
        c: n for c, n in tr["per_class"].items() if n != args.expected_train_per_class
    }
    wrong_test = {
        c: n for c, n in te["per_class"].items() if n != args.expected_test_per_class
    }

    dup_train = duplicate_groups(tr["hashes"])
    dup_test = duplicate_groups(te["hashes"])
    shared = set(tr["hashes"]) & set(te["hashes"])
    test_files_in_train = sorted(p for h in shared for p in te["hashes"][h])
    train_files_in_test = sorted(p for h in shared for p in tr["hashes"][h])

    report = {
        "dataset": "numbers 0-9 (existing split preserved)",
        "folders": {
            "train": TRAIN.relative_to(PROJECT_ROOT).as_posix(),
            "test": TEST.relative_to(PROJECT_ROOT).as_posix(),
        },
        "classes_found_train": sorted(tr["per_class"]),
        "classes_found_test": sorted(te["per_class"]),
        "missing_classes_train": missing_train,
        "missing_classes_test": missing_test,
        "unexpected_class_folders": extra,
        "images_per_class_train": tr["per_class"],
        "images_per_class_test": te["per_class"],
        "total_train_images": tr["total_images"],
        "total_test_images": te["total_images"],
        "classes_with_unexpected_train_count": wrong_train,
        "classes_with_unexpected_test_count": wrong_test,
        "train_image_sizes": tr["image_sizes"],
        "test_image_sizes": te["image_sizes"],
        "color_modes": {"train": tr["color_modes"], "test": te["color_modes"]},
        "channels": {"train": tr["channels"], "test": te["channels"]},
        "formats": {"train": tr["formats"], "test": te["formats"]},
        "corrupted_train": tr["corrupted"],
        "corrupted_test": te["corrupted"],
        "duplicate_groups_in_train": len(dup_train),
        "duplicate_files_in_train": sum(len(g) - 1 for g in dup_train),
        "duplicate_groups_in_test": len(dup_test),
        "duplicate_files_in_test": sum(len(g) - 1 for g in dup_test),
        "identical_content_groups_across_train_and_test": len(shared),
        "test_files_identical_to_a_train_file": len(test_files_in_train),
        "train_files_identical_to_a_test_file": len(train_files_in_test),
        "examples_test_files_identical_to_train": test_files_in_train[:10],
        "split_fingerprint_before_audit": fp_before,
        "split_unchanged_by_audit": fp_before
        == {"train": fingerprint(TRAIN), "test": fingerprint(TEST)},
        "variable_image_sizes": len(tr["image_sizes"]) + len(te["image_sizes"]) > 2,
        "recommendation": (
            "Evaluate on the cleaned test list (number_clean_manifest.json), which "
            "excludes test files whose content also appears in training. The original "
            "folders are untouched. Duplicates inside training are not deleted; "
            "resize all images to one size before training."
        ),
    }
    write_report("number_quality_report.json", report)

    excluded = set(test_files_in_train)
    all_test = [p for paths in te["hashes"].values() for p in paths]
    manifest = {
        "note": "Original folders untouched. Use these lists for honest evaluation.",
        "train_files": sorted(p for paths in tr["hashes"].values() for p in paths),
        "test_files_clean": sorted(p for p in all_test if p not in excluded),
        "test_files_excluded_as_leakage": sorted(excluded),
    }
    out = PROJECT_ROOT / "data" / "processed" / "number_clean_manifest.json"
    out.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print("Saved", out.relative_to(PROJECT_ROOT).as_posix())
    print(
        json.dumps(
            {
                k: report[k]
                for k in (
                    "total_train_images",
                    "total_test_images",
                    "missing_classes_train",
                    "missing_classes_test",
                    "classes_with_unexpected_train_count",
                    "classes_with_unexpected_test_count",
                    "color_modes",
                    "formats",
                    "duplicate_groups_in_train",
                    "duplicate_groups_in_test",
                    "test_files_identical_to_a_train_file",
                    "split_unchanged_by_audit",
                )
            },
            indent=2,
        )
    )
    for part, sizes in (("train", tr["image_sizes"]), ("test", te["image_sizes"])):
        top = sorted(sizes.items(), key=lambda kv: -kv[1])[:5]
        print(f"{part}: {len(sizes)} distinct image sizes; most common: {top}")
    print(
        "Clean test images:",
        len(manifest["test_files_clean"]),
        "| excluded as leakage:",
        len(excluded),
    )


if __name__ == "__main__":
    main()
