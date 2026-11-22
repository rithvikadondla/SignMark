"""Exploratory Data Analysis: charts and sample grid. Read-only on raw data.
Run from the project root:  python src/dataset_eda.py
Run src/inspect_dataset.py first (this script reads reports/dataset_summary.json).
"""

import json
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # no window needed, just save files
import matplotlib.pyplot as plt
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
from dataset_utils import REPORTS_DIR, find_split_dir, list_class_dirs, list_images


def plot_class_distribution(per_class):
    """Bar chart: number of training images per class."""
    fig, ax = plt.subplots(figsize=(12, 4.5))
    ax.bar(list(per_class), list(per_class.values()), color="#0B1F3A")
    ax.set_title("Training images per class")
    ax.set_xlabel("Class")
    ax.set_ylabel("Number of images")
    plt.xticks(rotation=60)
    plt.tight_layout()
    fig.savefig(REPORTS_DIR / "class_distribution.png", dpi=150)
    plt.close(fig)


def plot_sample_grid(class_dirs):
    """One example image per class in a grid (first image of each class)."""
    n = len(class_dirs)
    cols = 6
    rows = (n + cols - 1) // cols
    fig, axes = plt.subplots(rows, cols, figsize=(cols * 2.2, rows * 2.4))
    for ax in axes.ravel():
        ax.axis("off")
    for ax, d in zip(axes.ravel(), class_dirs):
        imgs = list_images(d)
        if imgs:
            ax.imshow(Image.open(imgs[0]).convert("RGB"))
        ax.set_title(d.name, fontsize=10)
    plt.tight_layout()
    fig.savefig(REPORTS_DIR / "sample_images.png", dpi=120)
    plt.close(fig)


def plot_image_sizes(sizes):
    """Bar chart of image dimensions found in the training set."""
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.bar(list(sizes), list(sizes.values()), color="#5B7DB1")
    ax.set_title("Training image dimensions")
    ax.set_ylabel("Number of images")
    plt.tight_layout()
    fig.savefig(REPORTS_DIR / "image_sizes.png", dpi=150)
    plt.close(fig)


def main():
    summary_file = REPORTS_DIR / "dataset_summary.json"
    if not summary_file.exists():
        sys.exit("Run python src/inspect_dataset.py first.")
    summary = json.loads(summary_file.read_text())
    class_dirs = list_class_dirs(find_split_dir("train"))
    plot_class_distribution(summary["images_per_class"])
    plot_sample_grid(class_dirs)
    plot_image_sizes(summary["train_image_sizes"])
    print(
        "Saved to reports/: class_distribution.png, sample_images.png, image_sizes.png"
    )


if __name__ == "__main__":
    main()
