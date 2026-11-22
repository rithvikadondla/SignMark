"""Load the cached arrays of one task (alphabet, numbers or phrases). No pandas.
Used by train_baseline.py and train_cnn.py."""
import json
from pathlib import Path

import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[1]
PROC = PROJECT_ROOT / "data" / "processed"
TASKS = {
    "alphabet": {"prefix": "", "labels": "label_map.json",
                 "size_file": "preprocess_info.json", "size_key": "image_size"},
    "numbers": {"prefix": "numbers_", "labels": "label_map_numbers.json",
                "size_file": "arrays_info.json", "size_key": "number_size"},
    "phrases": {"prefix": "phrases_", "labels": "label_map_phrases.json",
                "size_file": "arrays_info.json", "size_key": "phrase_size"},
}


def load_task(task, limit=0, seed=42):
    """Return dict: x_train, y_train, x_val, y_val, x_test, y_test (uint8 images, int labels),
    class_names (list ordered by label id) and size. limit>0 keeps a random subset of the
    TRAIN set only (for quick smoke tests)."""
    cfg = TASKS[task]
    size = json.loads((PROC / cfg["size_file"]).read_text())[cfg["size_key"]]
    label_map = json.loads((PROC / cfg["labels"]).read_text())
    class_names = [n for n, _ in sorted(label_map.items(), key=lambda kv: kv[1])]
    out = {"class_names": class_names, "size": size, "task": task}
    for split in ("train", "val", "test"):
        x = np.load(PROC / f"{cfg['prefix']}{split}_x_{size}.npy")
        y = np.load(PROC / f"{cfg['prefix']}{split}_y.npy")
        if limit and split == "train" and len(x) > limit:
            idx = np.random.default_rng(seed).permutation(len(x))[:limit]
            x, y = x[idx], y[idx]
        out[f"x_{split}"], out[f"y_{split}"] = x, y
    return out