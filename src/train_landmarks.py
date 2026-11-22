"""Train and evaluate landmark-based models (63 hand-landmark features) with scikit-learn.
Run from the project root (venv active):
    python src/train_landmarks.py                    (all three tasks, three models each)
    python src/train_landmarks.py --task numbers
Needs data/processed/signmark_landmarks.npz (from Colab). CPU only, no TensorFlow, no MediaPipe.

Models compared: Random Forest, SVM (RBF), small MLP. Each is trained on the train split, scored on
validation, and evaluated ONCE on the test split. Results use the same evaluation code as the image
models, so they appear together in reports/model_comparison.json.
Note: landmark models only see images where MediaPipe found a hand (and the alphabet is a subset),
so their test set is not identical to the image models' test set. The report states this.
"""

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.neural_network import MLPClassifier
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC

sys.path.insert(0, str(Path(__file__).resolve().parent))
from evaluation import evaluate
from task_data import PROC, TASKS

MODELS = {
    "random_forest": lambda seed: RandomForestClassifier(
        n_estimators=300, n_jobs=-1, random_state=seed
    ),
    "svm_rbf": lambda seed: make_pipeline(
        StandardScaler(), SVC(kernel="rbf", C=10, gamma="scale")
    ),
    "mlp": lambda seed: make_pipeline(
        StandardScaler(),
        MLPClassifier(
            hidden_layer_sizes=(128, 64),
            early_stopping=True,
            max_iter=300,
            random_state=seed,
        ),
    ),
}


def run_task(task, data, summary, seed):
    label_map = json.loads((PROC / TASKS[task]["labels"]).read_text())
    names_by_id = {v: k for k, v in label_map.items()}
    sp = {
        s: (data[f"{task}_{s}_X"], data[f"{task}_{s}_y"])
        for s in ("train", "val", "test")
    }
    present = sorted(set().union(*[set(y.tolist()) for _, y in sp.values()]))
    remap = {
        old: new for new, old in enumerate(present)
    }  # contiguous ids for the classes that have data
    names = [names_by_id[i] for i in present]
    missing = [names_by_id[i] for i in names_by_id if i not in remap]
    sp = {s: (X, np.array([remap[v] for v in y])) for s, (X, y) in sp.items()}
    (Xtr, ytr), (Xva, yva), (Xte, yte) = sp["train"], sp["val"], sp["test"]
    t = summary[task]["test"]
    print(
        f"\n{task}: train {len(Xtr)}, val {len(Xva)}, test {len(Xte)}, {len(names)} classes with data"
        + (f" (no landmarks at all for: {missing})" if missing else "")
    )
    for name, make in MODELS.items():
        t0 = time.time()
        clf = make(seed).fit(Xtr, ytr)
        seconds = round(time.time() - t0, 1)
        val_acc = float((clf.predict(Xva) == yva).mean())
        res = evaluate(
            task,
            f"landmarks_{name}",
            yte,
            clf.predict(Xte),
            names,
            extra={
                "train_seconds": seconds,
                "validation_accuracy": val_acc,
                "features": "63 normalised MediaPipe hand-landmark values",
                "test_images_tried": t["tried"],
                "test_images_with_hand": t["kept"],
                "classes_without_landmarks": missing,
            },
        )
        print(
            f"  {name:14s} val {val_acc:.4f} | TEST accuracy {res['accuracy']:.4f} | macro F1 "
            f"{res['f1_macro']:.4f} | {seconds}s"
        )


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--task", default="all", choices=["all", "alphabet", "numbers", "phrases"]
    )
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()
    f = PROC / "signmark_landmarks.npz"
    if not f.exists():
        sys.exit(
            "data/processed/signmark_landmarks.npz not found. Finish the Colab step first."
        )
    data = np.load(f)
    summary = json.loads(str(data["summary_json"]))
    for task in (
        ["alphabet", "numbers", "phrases"] if args.task == "all" else [args.task]
    ):
        run_task(task, data, summary, args.seed)


if __name__ == "__main__":
    main()
