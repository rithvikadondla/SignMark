"""Classical baseline for the model comparison: Random Forest (or SVM) on small grayscale pixels.
Run from the project root:
    python src/train_baseline.py --task numbers --model rf
    python src/train_baseline.py --task phrases --model svm
    python src/train_baseline.py --task alphabet --model rf      (can take several minutes)
Trains on the train split, reports validation accuracy, and evaluates ONCE on the test split.
Nothing is made up: all numbers come from this run and are saved to reports/.
"""

import argparse
import sys
import time
from pathlib import Path

import cv2
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from evaluation import evaluate
from task_data import load_task


def features(x, side=32):
    """uint8 RGB images -> flattened grayscale side x side vectors scaled to 0..1."""
    out = np.empty((len(x), side * side), dtype=np.float32)
    for i, img in enumerate(x):
        g = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
        out[i] = (
            cv2.resize(g, (side, side), interpolation=cv2.INTER_AREA).reshape(-1)
            / 255.0
        )
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--task", required=True, choices=["alphabet", "numbers", "phrases"])
    ap.add_argument("--model", default="rf", choices=["rf", "svm"])
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    d = load_task(args.task)
    print(
        f"{args.task}: train {len(d['x_train'])}, val {len(d['x_val'])}, test {len(d['x_test'])}, "
        f"{len(d['class_names'])} classes"
    )
    if args.model == "svm" and len(d["x_train"]) > 20000:
        sys.exit("SVM is too slow for this many training images. Use --model rf.")
    xtr, xva, xte = (features(d[f"x_{s}"]) for s in ("train", "val", "test"))
    if args.model == "rf":
        from sklearn.ensemble import RandomForestClassifier

        clf = RandomForestClassifier(
            n_estimators=300, n_jobs=-1, random_state=args.seed
        )
        name = "random_forest"
    else:
        from sklearn.svm import SVC

        clf = SVC(kernel="rbf", C=10, gamma="scale")
        name = "svm_rbf"
    t0 = time.time()
    clf.fit(xtr, d["y_train"])
    seconds = round(time.time() - t0, 1)
    val_acc = float((clf.predict(xva) == d["y_val"]).mean())
    print(f"trained in {seconds}s, validation accuracy {val_acc:.4f}")
    summary = evaluate(
        args.task,
        name,
        d["y_test"],
        clf.predict(xte),
        d["class_names"],
        extra={
            "train_seconds": seconds,
            "validation_accuracy": val_acc,
            "features": "grayscale 32x32 pixels",
        },
    )
    print(
        f"TEST accuracy {summary['accuracy']:.4f} | macro precision {summary['precision_macro']:.4f} "
        f"| macro recall {summary['recall_macro']:.4f} | macro F1 {summary['f1_macro']:.4f}"
    )
    print("Saved reports/ files starting with", f"{args.task}_{name}_test_")


if __name__ == "__main__":
    main()
