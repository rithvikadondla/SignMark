"""Final verification of all three datasets + generation of the written report.
Run from the project root:  python src/verify_datasets.py
Read-only on data. Writes:
    reports/dataset_verification.json
    reports/dataset_engineering_report.md   (an existing file is kept as *.previous_<time>.md)
Every number in the markdown comes from the JSON files and arrays, nothing is typed by hand.
"""

import hashlib
import json
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from audit_utils import PROJECT_ROOT, REPORTS_DIR, write_report

PROC = PROJECT_ROOT / "data" / "processed"
checks = []
overlaps = {}  # identical-image counts between splits (duplicates are accepted, reported only)


def check(name, ok, detail=""):
    checks.append({"check": name, "passed": bool(ok), "detail": detail})
    print(("PASS  " if ok else "FAIL  ") + name + (f"  [{detail}]" if detail else ""))


def info(name, detail):
    """Informational line: counted as passed, written to the report, never hidden."""
    checks.append({"check": name, "passed": True, "detail": detail, "kind": "info"})
    print("INFO  " + name + f"  [{detail}]")


def jload(path):
    p = Path(path)
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None


def row_hashes(x):
    return {hashlib.md5(r.tobytes()).hexdigest() for r in x}


def verify_arrays(tag, prefix, size, n_classes, expect=None):
    """Check shapes, label ranges, class coverage and train/val/test overlap for one dataset."""
    data = {}
    for s in ("train", "val", "test"):
        xf, yf = PROC / f"{prefix}{s}_x_{size}.npy", PROC / f"{prefix}{s}_y.npy"
        if not (xf.exists() and yf.exists()):
            check(f"{tag}: {s} arrays exist", False, f"{xf.name} / {yf.name}")
            return None
        data[s] = (np.load(xf, mmap_mode="r"), np.load(yf))
    for s, (x, y) in data.items():
        check(
            f"{tag}: {s} shape and labels consistent",
            len(x) == len(y)
            and x.ndim == 4
            and x.shape[3] == 3
            and x.dtype == np.uint8
            and (len(y) == 0 or (y.min() >= 0 and y.max() < n_classes)),
            f"{len(x)} images, {x.shape[1:]}",
        )
        present = len(set(y.tolist()))
        check(
            f"{tag}: {s} contains classes",
            present > 0,
            f"{present} of {n_classes} classes present",
        )
        if expect and s in expect:
            check(
                f"{tag}: {s} image count matches report",
                len(x) == expect[s],
                f"{len(x)} vs {expect[s]}",
            )
    hs = {s: row_hashes(data[s][0]) for s in data}
    for a, b in (("train", "val"), ("train", "test"), ("val", "test")):
        n = len(hs[a] & hs[b])
        overlaps[f"{tag} {a}/{b}"] = n
        info(
            f"{tag}: identical images shared by {a} and {b} (duplicates accepted)",
            f"{n} shared",
        )
    return {
        s: {
            "images": int(len(data[s][0])),
            "per_class": {
                int(k): int(v)
                for k, v in zip(*np.unique(data[s][1], return_counts=True))
            },
        }
        for s in data
    }


def main():
    # ---- Alphabet ----
    split = jload(PROC / "split_info.json")
    lm = jload(PROC / "label_map.json")
    pre = jload(PROC / "preprocess_info.json")
    summary = jload(REPORTS_DIR / "dataset_summary.json")
    quality = jload(REPORTS_DIR / "dataset_quality_report.json")
    alpha = None
    if split and lm and pre:
        size = pre["image_size"]
        alpha = verify_arrays(
            "alphabet",
            "",
            size,
            len(lm),
            {
                "train": split["train_images"],
                "val": split["val_images"],
                "test": split["test_images"],
            },
        )
        check("alphabet: 29 classes", len(lm) == 29, f"{len(lm)} classes")
    else:
        check("alphabet: split_info / label_map / preprocess_info exist", False)

    # ---- Numbers ----
    info = jload(PROC / "arrays_info.json")
    nlm, plm = (
        jload(PROC / "label_map_numbers.json"),
        jload(PROC / "label_map_phrases.json"),
    )
    nq, pq, ps = (
        jload(REPORTS_DIR / n)
        for n in (
            "number_quality_report.json",
            "phrase_quality_report.json",
            "phrase_split_info.json",
        )
    )
    nums = phr = None
    if info and nlm:
        nums = verify_arrays("numbers", "numbers_", info["number_size"], 10)
        check("numbers: ten classes 0-9", sorted(nlm) == [str(d) for d in range(10)])
        if nums and nq:
            check(
                "numbers: all original training images used (train + val)",
                nums["train"]["images"] + nums["val"]["images"]
                == nq["total_train_images"],
                f"{nums['train']['images'] + nums['val']['images']} vs {nq['total_train_images']}",
            )
            check(
                "numbers: all original test images used",
                nums["test"]["images"] == nq["total_test_images"],
                f"{nums['test']['images']} vs {nq['total_test_images']}",
            )
        if nums:
            check(
                "numbers: every class present in train, val and test",
                all(len(nums[s]["per_class"]) == 10 for s in nums),
            )
        check(
            "numbers: original split preserved by the audit",
            bool(nq and nq.get("split_unchanged_by_audit")),
        )
    else:
        check(
            "numbers: arrays_info.json and label map exist (run prepare_arrays.py)",
            False,
        )
    if info and plm:
        phr = verify_arrays("phrases", "phrases_", info["phrase_size"], len(plm))
        check("phrases: 44 classes", len(plm) == 44, f"{len(plm)} classes")
        if phr:
            check(
                "phrases: every class present in train, val and test",
                all(len(phr[s]["per_class"]) == len(plm) for s in phr),
            )
            check(
                "phrases: test is 8 images per class",
                all(v == 8 for v in phr["test"]["per_class"].values()),
            )
        check(
            "phrases: split counts 1408 train+val and 352 test",
            bool(phr)
            and phr["train"]["images"] + phr["val"]["images"] == 1408
            and phr["test"]["images"] == 352,
        )
        check("phrases: raw folder unchanged", bool(ps and ps.get("raw_unchanged")))
        check(
            "phrases: no train/test overlap in the file split",
            bool(ps)
            and ps.get("file_name_overlap_train_test") == 0
            and ps.get("identical_content_overlap_train_test") == 0,
        )

    for name in (
        "dataset_summary.json",
        "dataset_quality_report.json",
        "number_quality_report.json",
        "phrase_quality_report.json",
        "phrase_split_info.json",
    ):
        check(f"report exists: {name}", (REPORTS_DIR / name).exists())

    result = {
        "generated": time.strftime("%Y-%m-%d %H:%M:%S"),
        "all_passed": all(c["passed"] for c in checks),
        "checks": checks,
        "identical_image_overlaps_between_splits": overlaps,
        "alphabet": alpha,
        "numbers": nums,
        "phrases": phr,
    }
    write_report("dataset_verification.json", result)
    write_markdown(summary, quality, split, pre, info, nq, pq, ps, result)
    print(
        "\nALL CHECKS PASSED"
        if result["all_passed"]
        else "\nSOME CHECKS FAILED - see FAIL lines above"
    )


def fmt(d):
    return ", ".join(f"{k}: {v}" for k, v in d.items()) if d else "n/a"


def write_markdown(summary, quality, split, pre, info, nq, pq, ps, result):
    L = [
        "# SignMark - Dataset Engineering Report",
        "",
        f"*Generated automatically from the project's JSON reports on {result['generated']}.*",
        "",
    ]
    L += [
        "## Verification",
        "",
        f"Overall: **{'all checks passed' if result['all_passed'] else 'some checks FAILED'}** "
        f"({sum(c['passed'] for c in result['checks'])}/{len(result['checks'])}). "
        "Details: `reports/dataset_verification.json`.",
        "",
    ]
    if summary:
        L += [
            "## 1. Alphabet dataset (ASL Alphabet, Kaggle `grassknoted/asl-alphabet`)",
            "",
            f"- Classes: {summary['num_classes']} ({', '.join(summary['classes'])})",
            f"- Training images: {summary['total_train_images']}; official test images: {summary['total_test_images']}",
            f"- Image sizes: {fmt(summary['train_image_sizes'])}; colour: {fmt(summary['train_color_modes'])}; "
            f"format: {fmt(summary['train_formats'])}",
            f"- Class imbalance (max/min): {summary['imbalance_max_over_min']}",
        ]
    if quality:
        L += [
            f"- Corrupted images: {len(quality['corrupted_train'])} train, {len(quality['corrupted_test'])} test",
            f"- Exact duplicates in training: {quality['duplicate_images_in_train']}",
            f"- Official test files identical to training files: {quality['identical_files_in_train_and_test']} "
            "(the official test folder is therefore NOT used for evaluation)",
        ]
    if split:
        L += [
            f"- Own split: train {split['train_images']}, validation {split['val_images']}, test {split['test_images']} "
            f"(seed {split['seed']}, block size {split.get('block_size', 'n/a')}, no shared files)"
        ]
    if pre:
        L += [
            f"- Cached arrays: {pre['image_size']}x{pre['image_size']}, uint8 RGB, normalised at training time"
        ]
    if nq:
        L += [
            "",
            "## 2. Number dataset (digits 0-9)",
            "",
            f"- Original split preserved: train {nq['total_train_images']}, test {nq['total_test_images']}",
            f"- Missing classes: train {nq['missing_classes_train']}, test {nq['missing_classes_test']}",
            f"- Classes with unexpected counts: train {nq['classes_with_unexpected_train_count']}, "
            f"test {nq['classes_with_unexpected_test_count']}",
            f"- Distinct image sizes: train {len(nq['train_image_sizes'])}, test {len(nq['test_image_sizes'])} "
            f"(all resized to one size for training)",
            f"- Colour modes: {nq['color_modes']}; formats: {nq['formats']}",
            f"- Corrupted: {len(nq['corrupted_train'])} train, {len(nq['corrupted_test'])} test",
            f"- Duplicate groups: {nq['duplicate_groups_in_train']} in train, {nq['duplicate_groups_in_test']} in test",
            f"- Duplicates accepted by the team: {nq['test_files_identical_to_a_train_file']} test files are identical "
            f"to a training file ({nq['test_files_identical_to_a_train_file'] / nq['total_test_images']:.2%} of the test set). "
            "Nothing was excluded, so test scores may be slightly optimistic. Originals are untouched.",
        ]
    if info and "numbers" in info:
        n = info["numbers"]
        L += [
            f"- Arrays ({info['number_size']}x{info['number_size']}): train {n['train']['images']}, "
            f"validation {n['val']['images']} (from train only), test {n['test']['images']} (all original test images)"
        ]
    if pq:
        L += [
            "",
            "## 3. Phrase dataset (static images)",
            "",
            f"- Classes: {pq['classes_found']} (expected {pq['expected_classes']}); images: {pq['total_images']}",
            f"- Classes with unexpected counts: {pq['classes_with_unexpected_count']}",
            f"- Sizes: {fmt(pq['image_sizes'])}; colour: {fmt(pq['color_modes'])}; formats: {fmt(pq['formats'])}",
            f"- Corrupted: {len(pq['corrupted_images'])}; duplicate files: {pq['duplicate_files']}",
            f"- Raw folder: `{pq.get('raw_folder', 'n/a')}`; unchanged by the scripts: {pq.get('raw_unchanged')}",
            f"- Identical images appearing in more than one class: "
            f"{pq.get('identical_images_in_more_than_one_class', 'n/a')} (a label conflict if above 0)",
        ]
    if ps:
        L += [
            f"- Split (seed {ps['seed']}, per-class, identical copies kept together): train {ps['train_images']} "
            f"({ps.get('unique_train_images', 'n/a')} unique), test {ps['test_images']} "
            f"({ps.get('unique_test_images', 'n/a')} unique); "
            f"overlap: {ps['file_name_overlap_train_test']} by name, {ps['identical_content_overlap_train_test']} by content"
        ]
    if info and "phrases" in info:
        p = info["phrases"]
        L += [
            f"- Arrays ({info['phrase_size']}x{info['phrase_size']}): train {p['train']['images']}, "
            f"validation {p['val']['images']} (from train only), test {p['test']['images']}"
        ]
    ov = result.get("identical_image_overlaps_between_splits", {})
    L += [
        "",
        "## 4. Duplicates (accepted)",
        "",
        "The team decided to keep duplicate images. After resizing, identical images shared between splits:",
        "",
    ]
    L += [f"- {k}: {v}" for k, v in ov.items()] or ["- not computed"]
    L += [
        "",
        "Because of this, validation scores (and, for numbers, a small part of the test set) can be slightly "
        "optimistic. Phrase train/test were split so identical copies stay together.",
        "",
    ]
    L += [
        "## 5. Limitations",
        "",
        "- Alphabet images show little variety in setting and signer, so test scores will be more "
        "optimistic than real webcam use; near-identical neighbouring frames may still exist across splits.",
        "- J and Z are motion signs; `del`, `nothing`, `space` are control classes.",
        "- The phrase set has few images per class (40), and still images cannot capture movement; "
        "the phrase model only recognises the still poses in this dataset.",
        "- The language and source/licence of the number and phrase datasets must be documented by the team; "
        "they were collected outside these scripts.",
        "- Signer identity is unknown, so signer-independent evaluation is not possible.",
        "",
        "## 6. Generated files",
        "",
        "- `reports/`: dataset_summary, dataset_quality_report, number_quality_report, phrase_quality_report, "
        "phrase_split_info, dataset_verification (JSON); charts; this report",
        "- `data/processed/`: split manifests, label maps, `arrays_info.json`, cached `.npy` arrays "
        "(alphabet, numbers_*, phrases_*), `phrases/train|test` image copies, number_clean_manifest.json",
        "",
    ]
    out = REPORTS_DIR / "dataset_engineering_report.md"
    if out.exists():
        out.rename(
            out.with_name(
                f"dataset_engineering_report.previous_{time.strftime('%Y%m%d_%H%M%S')}.md"
            )
        )
    out.write_text("\n".join(L), encoding="utf-8")
    print("Saved reports/dataset_engineering_report.md")


if __name__ == "__main__":
    main()
