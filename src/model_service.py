"""Loads the trained Keras models ONCE and predicts on one RGB image.
Kept separate from the Flask routes so models can be swapped without touching the API.

Preprocessing must match how each task's training arrays were made:
  alphabet : PIL resize, bilinear (src/preprocess_dataset.py)
  numbers  : OpenCV resize, INTER_AREA (src/prepare_arrays.py)
  phrases  : OpenCV resize, INTER_AREA (src/prepare_arrays.py)
The saved models rescale pixels themselves, so we feed raw 0-255 RGB values.
"""
import json
import threading
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

PROJECT_ROOT = Path(__file__).resolve().parents[1]
TASKS = ("alphabet", "numbers", "phrases")
ALIASES = {"alphabet": "alphabet", "number": "numbers", "numbers": "numbers",
           "phrase": "phrases", "phrases": "phrases"}
RESIZE = {"alphabet": "pil_bilinear", "numbers": "cv2_area", "phrases": "cv2_area"}
DEFAULT_THRESHOLD = 0.80


def normalize_mode(mode):
    """'number' -> 'numbers', etc. Returns None for an unknown mode."""
    return ALIASES.get(str(mode).strip().lower()) if mode is not None else None


def resize_for(task, rgb, size):
    if RESIZE[task] == "pil_bilinear":
        return np.asarray(Image.fromarray(rgb).resize((size, size), Image.BILINEAR), dtype=np.float32)
    return cv2.resize(rgb, (size, size), interpolation=cv2.INTER_AREA).astype(np.float32)


class ModelService:
    def __init__(self, models_dir=None):
        self.models_dir = Path(models_dir) if models_dir else PROJECT_ROOT / "models"
        self._models, self._meta, self._errors = {}, {}, {}
        self._lock = threading.Lock()
        for task in TASKS:
            f = self.models_dir / f"{task}_meta.json"
            if f.exists() and (self.models_dir / f"{task}_model.keras").exists():
                self._meta[task] = json.loads(f.read_text(encoding="utf-8"))

    # ----- information -----
    def available(self, task):
        return task in self._meta

    def class_names(self, task):
        return list(self._meta[task]["class_names"]) if self.available(task) else []

    def threshold(self, task):
        t = self._meta.get(task, {}).get("suggested_confidence_threshold")
        return float(t) if t else DEFAULT_THRESHOLD

    def status(self):
        return {t: {"available": self.available(t), "loaded": t in self._models,
                    "error": self._errors.get(t)} for t in TASKS}

    # ----- loading -----
    def load(self, task):
        if task in self._models or not self.available(task):
            return
        try:
            import tensorflow as tf   # imported only when a model is really needed
            self._models[task] = tf.keras.models.load_model(
                self.models_dir / f"{task}_model.keras", compile=False)
            self._errors.pop(task, None)
        except Exception as e:        # keep the server alive; report the problem in /api/health
            self._errors[task] = f"{type(e).__name__}: {e}"

    def load_all(self):
        for task in TASKS:
            self.load(task)

    # ----- prediction -----
    def predict(self, task, rgb):
        """rgb: uint8 array (H, W, 3). Returns a plain dict (no Flask objects)."""
        if not self.available(task):
            raise LookupError(f"No trained model for '{task}'")
        self.load(task)
        if task not in self._models:
            raise RuntimeError(self._errors.get(task, "model could not be loaded"))
        size = int(self._meta[task]["input_size"])
        x = resize_for(task, rgb, size)[None, ...]
        with self._lock:                                   # Keras models are not thread-safe
            probs = np.asarray(self._models[task](x, training=False))[0]
        names = self.class_names(task)
        order = np.argsort(probs)[::-1]
        top3 = [{"label": names[i], "confidence": round(float(probs[i]), 4)} for i in order[:3]]
        best, conf, thr = names[order[0]], float(probs[order[0]]), self.threshold(task)
        if conf < thr:
            status, label, message = "uncertain", None, "Not sure. Hold the sign steady and try again."
        elif task == "alphabet" and best == "nothing":
            status, label, message = "no_hand", None, "No hand sign detected in the frame."
        else:
            status, label, message = "confident", best, "Prediction made"
        return {"status": status, "label": label, "confidence": round(conf, 4),
                "top3": top3, "threshold": thr, "message": message}
