"""Check the single landmark file downloaded from Colab (NumPy only, no MediaPipe needed).
Run from the project root:  python src/verify_landmarks.py
Expects data/processed/signmark_landmarks.npz. Writes reports/landmark_verification.json.
Phase 4 counts as complete only when this prints ALL CHECKS PASSED."""

import json
import sys
from collections import Counter
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from audit_utils import PROJECT_ROOT, write_report

PROC = PROJECT_ROOT / "data" / "processed"
LABELS = {
    "alphabet": "label_map.json",
    "numbers": "label_map_numbers.json",
    "phrases": "label_map_phrases.json",
}
checks = []


def check(name, ok, detail=""):
    checks.append({"check": name, "passed": bool(ok), "detail": detail})
    print(("PASS  " if ok else "FAIL  ") + name + (f"  [{detail}]" if detail else ""))


def main():
    f = PROC / "signmark_landmarks.npz"
    if not f.exists():
        sys.exit(
            "data/processed/signmark_landmarks.npz not found. Download it from Colab first."
        )
    d = np.load(f)
    summary = json.loads(str(d["summary_json"]))
    out = {}
    for ds, lm_file in LABELS.items():
        n_classes = len(json.loads((PROC / lm_file).read_text()))
        seen, out[ds] = {}, {}
        for split in ("train", "val", "test"):
            tag = f"{ds} {split}"
            X, y, paths = (
                d[f"{ds}_{split}_X"],
                d[f"{ds}_{split}_y"],
                d[f"{ds}_{split}_paths"],
            )
            s = summary[ds][split]
            check(
                f"{tag}: shape (n, 63), finite, counts agree",
                X.ndim == 2
                and X.shape[1] == 63
                and np.isfinite(X).all()
                and len(X) == len(y) == len(paths) == s["kept"],
                f"{X.shape}",
            )
            check(
                f"{tag}: wrist at origin",
                len(X) > 0 and np.allclose(X[:, :3], 0, atol=1e-5),
            )
            check(
                f"{tag}: labels in range",
                len(y) > 0 and 0 <= y.min() and y.max() < n_classes,
                f"{len(set(y.tolist()))} classes present",
            )
            dup = [p for p in paths.tolist() if p in seen]
            check(
                f"{tag}: no image also in another split", not dup, f"{len(dup)} clashes"
            )
            seen.update({p: split for p in paths.tolist()})
            reasons = Counter(x["reason"] for x in s["skipped"])
            out[ds][split] = {
                "tried": s["tried"],
                "kept": s["kept"],
                "skipped": len(s["skipped"]),
                "kept_rate": round(s["kept"] / s["tried"], 4),
                "skip_reasons": dict(reasons),
                "classes_present": len(set(y.tolist())),
                "classes_total": n_classes,
            }
            print(
                f"      kept {s['kept']} of {s['tried']} ({s['kept'] / s['tried']:.1%}); skipped: {dict(reasons)}"
            )
    result = {
        "all_passed": all(c["passed"] for c in checks),
        "checks": checks,
        "summary": out,
    }
    write_report("landmark_verification.json", result)
    print(
        "\nALL CHECKS PASSED"
        if result["all_passed"]
        else "\nSOME CHECKS FAILED - see FAIL lines"
    )


if __name__ == "__main__":
    main()
