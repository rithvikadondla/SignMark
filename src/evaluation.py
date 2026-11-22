"""Shared evaluation code: metrics, classification report, confusion matrix, curves.
Uses only numpy, scikit-learn and matplotlib (no pandas, no TensorFlow).
Results go to reports/ and are what the Model Insights page will show."""

import json
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    precision_recall_fscore_support,
)

sys.path.insert(0, str(Path(__file__).resolve().parent))
from audit_utils import REPORTS_DIR, write_report


def evaluate(task, model_name, y_true, y_pred, class_names, split="test", extra=None):
    """Compute and save all metrics for one model on one split. Returns the summary dict."""
    labels = list(range(len(class_names)))
    y_true, y_pred = np.asarray(y_true), np.asarray(y_pred)
    summary = {
        "task": task,
        "model": model_name,
        "split": split,
        "images": int(len(y_true)),
        "accuracy": float(accuracy_score(y_true, y_pred)),
    }
    for avg in ("macro", "weighted"):
        p, r, f, _ = precision_recall_fscore_support(
            y_true, y_pred, labels=labels, average=avg, zero_division=0
        )
        summary.update(
            {
                f"precision_{avg}": float(p),
                f"recall_{avg}": float(r),
                f"f1_{avg}": float(f),
            }
        )
    report = classification_report(
        y_true,
        y_pred,
        labels=labels,
        target_names=class_names,
        output_dict=True,
        zero_division=0,
    )
    cm = confusion_matrix(y_true, y_pred, labels=labels)
    summary["per_class"] = {
        c: {k: float(v) if k != "support" else int(v) for k, v in report[c].items()}
        for c in class_names
    }
    summary["confusion_matrix"] = cm.tolist()
    summary["classes_never_predicted"] = [
        class_names[i] for i in labels if cm[:, i].sum() == 0
    ]
    if extra:
        summary.update(extra)
    stem = f"{task}_{model_name}_{split}"
    (REPORTS_DIR / f"{stem}_evaluation.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )
    (REPORTS_DIR / f"{stem}_classification_report.txt").write_text(
        classification_report(
            y_true,
            y_pred,
            labels=labels,
            target_names=class_names,
            zero_division=0,
            digits=4,
        ),
        encoding="utf-8",
    )
    plot_confusion(
        cm,
        class_names,
        REPORTS_DIR / f"{stem}_confusion_matrix.png",
        f"{task} / {model_name} / {split}: confusion matrix (row-normalised)",
    )
    update_comparison(summary)
    return summary


def plot_confusion(cm, class_names, path, title):
    n = len(class_names)
    norm = cm / np.maximum(cm.sum(axis=1, keepdims=True), 1)
    size = max(6, n * 0.32)
    fig, ax = plt.subplots(figsize=(size, size))
    im = ax.imshow(norm, cmap="Blues", vmin=0, vmax=1)
    ax.set_xticks(range(n))
    ax.set_yticks(range(n))
    ax.set_xticklabels(class_names, rotation=90, fontsize=max(5, 11 - n // 8))
    ax.set_yticklabels(class_names, fontsize=max(5, 11 - n // 8))
    ax.set_xlabel("Predicted")
    ax.set_ylabel("True")
    ax.set_title(title, fontsize=10)
    fig.colorbar(im, fraction=0.046)
    plt.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def plot_history(task, model_name, history):
    """history: dict of lists, e.g. loss, val_loss, accuracy, val_accuracy."""
    fig, axes = plt.subplots(1, 2, figsize=(10, 3.8))
    for ax, key, title in (
        (axes[0], "loss", "Loss"),
        (axes[1], "accuracy", "Accuracy"),
    ):
        if key in history:
            ax.plot(history[key], label="train")
        if f"val_{key}" in history:
            ax.plot(history[f"val_{key}"], label="validation")
        ax.set_title(title)
        ax.set_xlabel("Epoch")
        ax.legend()
    plt.tight_layout()
    fig.savefig(REPORTS_DIR / f"{task}_{model_name}_training_history.png", dpi=150)
    plt.close(fig)


def update_comparison(summary):
    """Keep reports/model_comparison.json: one entry per task and model (latest run)."""
    path = REPORTS_DIR / "model_comparison.json"
    data = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
    keys = (
        "split",
        "images",
        "accuracy",
        "precision_macro",
        "recall_macro",
        "f1_macro",
        "precision_weighted",
        "recall_weighted",
        "f1_weighted",
    )
    entry = {k: summary[k] for k in keys}
    entry.update(
        {k: summary[k] for k in ("train_seconds", "parameters") if k in summary}
    )
    data.setdefault(summary["task"], {})[summary["model"]] = entry
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")

def suggest_threshold(probs, y_true, target_accuracy=0.95):
    """Confidence threshold chosen on VALIDATION data: the lowest value in 0.50..0.99 for
    which predictions above it reach target_accuracy. Returns (threshold or None, details)."""
    probs, y_true = np.asarray(probs), np.asarray(y_true)
    conf, pred = probs.max(axis=1), probs.argmax(axis=1)
    for t in np.round(np.arange(0.50, 0.995, 0.01), 2):
        keep = conf >= t
        if keep.sum() >= 20 and (pred[keep] == y_true[keep]).mean() >= target_accuracy:
            return float(t), {
                "coverage": float(keep.mean()),
                "accuracy_above_threshold": float((pred[keep] == y_true[keep]).mean()),
            }
    return None, {
        "note": f"no threshold reached {target_accuracy:.0%} accuracy on validation data"
    }
