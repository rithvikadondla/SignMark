"""Phase 6: build the Model Insights data from the REAL evaluation results.
Run from the project root after training:  python src/model_insights.py
Reads reports/<task>_<model>_test_evaluation.json (made by train_cnn.py, train_baseline.py and
train_landmarks.py). Writes reports/model_insights.json (for the website), reports/model_comparison.png
and reports/per_class_f1.png. Nothing here is typed by hand: every number comes from those files.
The 'best' model is chosen by VALIDATION accuracy, never by test accuracy.
The insights (weakest classes, confusions, confusion-matrix image) describe the DEPLOYED model, i.e.
the one saved in models/<task>_meta.json that the website actually uses."""

import json
import sys
import time
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

REPORTS = Path(__file__).resolve().parents[1] / "reports"
MODELS = Path(__file__).resolve().parents[1] / "models"
TASKS = ("alphabet", "numbers", "phrases")


def load_runs():
    runs = {t: [] for t in TASKS}
    for f in sorted(REPORTS.glob("*_test_evaluation.json")):
        if ".previous_" in f.name:
            continue
        r = json.loads(f.read_text(encoding="utf-8"))
        if r.get("task") in runs:
            runs[r["task"]].append(r)
    return runs


def deployed_name(task):
    """Name of the model the website uses for this task (from models/<task>_meta.json), or None."""
    f = MODELS / f"{task}_meta.json"
    return (
        json.loads(f.read_text(encoding="utf-8")).get("model") if f.exists() else None
    )


def family(model):
    return "landmarks" if model.startswith("landmarks_") else "image"


def top_confusions(r, k=5):
    cm, names = np.array(r["confusion_matrix"]), r["per_class"]
    names = list(names)
    pairs = [
        (int(cm[i, j]), names[i], names[j])
        for i in range(len(cm))
        for j in range(len(cm))
        if i != j and cm[i, j] > 0
    ]
    pairs.sort(reverse=True)
    return [{"true": a, "predicted_as": b, "count": n} for n, a, b in pairs[:k]]


def task_insights(task, runs):
    if not runs:
        return {
            "available": False,
            "message": "No evaluation results for this task yet.",
        }
    models = []
    for r in runs:
        m = {
            k: r.get(k)
            for k in (
                "model",
                "images",
                "accuracy",
                "precision_macro",
                "recall_macro",
                "f1_macro",
                "precision_weighted",
                "recall_weighted",
                "f1_weighted",
                "validation_accuracy",
                "train_seconds",
                "parameters",
                "features",
            )
        }
        m["family"] = family(r["model"])
        if m["family"] == "landmarks":
            m["test_images_with_hand"] = r.get("test_images_with_hand")
            m["test_images_tried"] = r.get("test_images_tried")
        models.append(m)
    models.sort(key=lambda m: m["model"])
    scored = [r for r in runs if r.get("validation_accuracy") is not None]
    best = max(
        scored or runs,
        key=lambda r: r.get("validation_accuracy") if scored else r["accuracy"],
    )
    dep_name = deployed_name(task)
    deployed = next((r for r in runs if r["model"] == dep_name), None)
    focus = deployed or best
    support = {c: v["support"] for c, v in focus["per_class"].items()}
    f1 = sorted(
        (v["f1-score"], c) for c, v in focus["per_class"].items() if v["support"] > 0
    )
    notes = []
    if deployed is None:
        notes.append(
            "No saved model was found for this task, so the details below describe the best model by validation accuracy."
        )
    elif deployed["model"] != best["model"]:
        notes.append(
            f"The best validation score belongs to '{best['model']}', which the website does not use. "
            f"The details below describe the deployed model '{deployed['model']}'."
        )
    if (
        focus.get("validation_accuracy") is not None
        and focus["validation_accuracy"] - focus["accuracy"] > 0.05
    ):
        notes.append(
            f"Validation accuracy ({focus['validation_accuracy']:.3f}) is more than 5 points above test accuracy "
            f"({focus['accuracy']:.3f}): the model may be over-fitted to the training/validation data."
        )
    if focus.get("mean_confidence_when_wrong") is not None:
        notes.append(
            f"Mean confidence when correct {focus['mean_confidence_when_correct']:.3f} vs when wrong "
            f"{focus['mean_confidence_when_wrong']:.3f}."
        )
    if focus.get("classes_never_predicted"):
        notes.append(
            f"Never predicted on the test set: {', '.join(focus['classes_never_predicted'])}."
        )
    simple = [
        r
        for r in runs
        if r["model"] in ("random_forest", "svm_rbf") and r["accuracy"] >= 0.99
    ]
    if simple:
        notes.append(
            f"A simple pixel baseline ({simple[0]['model']}) reaches {simple[0]['accuracy']:.1%} on this test set, "
            "which suggests the test images are very similar to the training images; real-world accuracy may be lower."
        )
    if any(family(r["model"]) == "landmarks" for r in runs):
        notes.append(
            "Landmark models are evaluated only on test images where a hand was detected "
            "(and, for the alphabet, on a subset), so their test set differs from the image models'."
        )
    for m in models:
        m["deployed"] = m["model"] == dep_name
    out = {
        "available": True,
        "models": models,
        "best_by_validation": {
            "model": best["model"],
            "selected_using": "validation accuracy"
            if scored
            else "test accuracy (no validation score available)",
            "test_accuracy": best["accuracy"],
            "f1_macro": best["f1_macro"],
        },
        "deployed_model": None
        if deployed is None
        else {
            "model": deployed["model"],
            "test_accuracy": deployed["accuracy"],
            "f1_macro": deployed["f1_macro"],
            "validation_accuracy": deployed.get("validation_accuracy"),
            "used_by_website": True,
        },
        "details_describe": focus["model"],
        "weakest_classes": [
            {"class": c, "f1": round(v, 4), "test_images": support[c]}
            for v, c in f1[:5]
        ],
        "most_confused_pairs": top_confusions(focus),
        "notes": notes,
        "confusion_matrix_file": f"{task}_{focus['model']}_test_confusion_matrix.png",
    }
    return out


def charts(runs):
    fig, axes = plt.subplots(1, 3, figsize=(15, 4.2))
    for ax, task in zip(axes, TASKS):
        rs = sorted(runs[task], key=lambda r: r["model"])
        ax.set_title(task)
        if not rs:
            ax.text(0.5, 0.5, "no results yet", ha="center", transform=ax.transAxes)
            continue
        x = np.arange(len(rs))
        ax.bar(
            x - 0.2, [r["accuracy"] for r in rs], 0.4, label="accuracy", color="#0B1F3A"
        )
        ax.bar(
            x + 0.2, [r["f1_macro"] for r in rs], 0.4, label="macro F1", color="#5B7DB1"
        )
        ax.set_xticks(x)
        ax.set_xticklabels(
            [r["model"].replace("landmarks_", "lm_") for r in rs],
            rotation=40,
            ha="right",
            fontsize=8,
        )
        ax.set_ylim(0, 1)
        ax.legend(fontsize=8)
    plt.suptitle("Test-set comparison (real results)")
    plt.tight_layout()
    fig.savefig(REPORTS / "model_comparison.png", dpi=150)
    plt.close(fig)

    fig, axes = plt.subplots(1, 3, figsize=(15, 8))
    for ax, task in zip(axes, TASKS):
        rs = runs[task]
        ax.set_title(task)
        if not rs:
            ax.axis("off")
            continue
        scored = [r for r in rs if r.get("validation_accuracy") is not None]
        best = next((r for r in rs if r["model"] == deployed_name(task)), None) or max(
            scored or rs,
            key=lambda r: r.get("validation_accuracy") if scored else r["accuracy"],
        )
        items = sorted(
            (v["f1-score"], c) for c, v in best["per_class"].items() if v["support"] > 0
        )
        ax.barh([c for _, c in items], [v for v, _ in items], color="#5B7DB1")
        ax.set_xlim(0, 1)
        ax.tick_params(axis="y", labelsize=max(5, 9 - len(items) // 10))
        ax.set_xlabel(f"F1 per class (deployed: {best['model']})")
    plt.tight_layout()
    fig.savefig(REPORTS / "per_class_f1.png", dpi=150)
    plt.close(fig)


def main():
    runs = load_runs()
    if not any(runs.values()):
        sys.exit(
            "No *_test_evaluation.json files in reports/. Train and evaluate models first."
        )
    out = {
        "generated": time.strftime("%Y-%m-%d %H:%M:%S"),
        "source": "reports/<task>_<model>_test_evaluation.json (real runs only)",
        "tasks": {t: task_insights(t, runs[t]) for t in TASKS},
        "limitations": [
            "Duplicate images were kept, so validation scores and part of the number test set may be slightly optimistic.",
            "Alphabet photos come from one capture setting; real webcam accuracy is expected to be lower.",
            "Phrase classes have few images (40 per class) and are still images, not movements.",
            "The test sets are used once; the best model is chosen on validation accuracy.",
        ],
    }
    (REPORTS / "model_insights.json").write_text(
        json.dumps(out, indent=2), encoding="utf-8"
    )
    charts(runs)
    for t in TASKS:
        i = out["tasks"][t]
        if not i["available"]:
            print(f"{t}: no results yet")
            continue
        b = i["best_by_validation"]
        dep = i["deployed_model"]["model"] if i["deployed_model"] else "none found"
        print(
            f"{t}: {len(i['models'])} models; best by validation = {b['model']} "
            f"(test accuracy {b['test_accuracy']:.4f}, macro F1 {b['f1_macro']:.4f}); deployed = {dep}"
        )
        for m in i["models"]:
            print(
                f"  {'*' if m.get('deployed') else ' '} {m['model']:26s} acc {m['accuracy']:.4f}  P {m['precision_macro']:.4f}  R {m['recall_macro']:.4f}  F1 {m['f1_macro']:.4f}"
            )
    print("Saved reports/model_insights.json, model_comparison.png, per_class_f1.png")


if __name__ == "__main__":
    main()
