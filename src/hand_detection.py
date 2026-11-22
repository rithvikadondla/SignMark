"""Hand detection and landmark features using MediaPipe HandLandmarker (Tasks API).

The same functions are used for training (extract_landmarks.py) and for the Flask
backend, so features are identical in both places.
"""

import hashlib
import sys
import urllib.request
from pathlib import Path

import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[1]
MODEL_PATH = PROJECT_ROOT / "models" / "hand_landmarker.task"
MODEL_URL = (
    "https://storage.googleapis.com/mediapipe-models/hand_landmarker/"
    "hand_landmarker/float16/1/hand_landmarker.task"
)
# SHA-256 published for the float16 / version 1 file (checked as a warning only)
MODEL_SHA256 = "fbc2a30080c3c557093b5ddfc334698132eb341044ccee322ccf8bcf3607cde1"
NUM_FEATURES = 63  # 21 landmarks x (x, y, z)


def ensure_model():
    """Download the official MediaPipe hand model once into models/."""
    if MODEL_PATH.exists() and MODEL_PATH.stat().st_size > 0:
        return MODEL_PATH
    MODEL_PATH.parent.mkdir(exist_ok=True)
    print(f"Downloading hand model to {MODEL_PATH} ...")
    urllib.request.urlretrieve(MODEL_URL, MODEL_PATH)
    digest = hashlib.sha256(MODEL_PATH.read_bytes()).hexdigest()
    if digest != MODEL_SHA256:
        print("WARNING: model checksum differs from the published one:", digest)
    return MODEL_PATH


def normalize_landmarks(points):
    """points: (21, 3) array of x, y, z. Returns a flat 63-feature vector, or None.

    Translate so the wrist (landmark 0) is the origin, then divide by the largest
    hand size in the x-y plane. This removes position and size of the hand in the
    image, so only the hand shape remains.
    """
    pts = np.asarray(points, dtype=np.float32).reshape(21, 3)
    pts = pts - pts[0]
    scale = float(np.max(np.linalg.norm(pts[:, :2], axis=1)))
    if scale < 1e-6:
        return None
    return (pts / scale).reshape(-1)


class HandDetector:
    """Wraps MediaPipe HandLandmarker for single still images."""

    def __init__(self, min_confidence=0.5):
        import mediapipe as mp
        from mediapipe.tasks import python as mp_python
        from mediapipe.tasks.python import vision

        self._mp = mp
        options = vision.HandLandmarkerOptions(
            base_options=mp_python.BaseOptions(model_asset_path=str(ensure_model())),
            running_mode=vision.RunningMode.IMAGE,
            num_hands=1,
            min_hand_detection_confidence=min_confidence,
        )
        self._landmarker = vision.HandLandmarker.create_from_options(options)

    def detect(self, rgb_image):
        """rgb_image: uint8 array (H, W, 3) in RGB order.
        Returns raw landmarks as a (21, 3) array, or None if no hand is found."""
        image = self._mp.Image(
            image_format=self._mp.ImageFormat.SRGB, data=np.ascontiguousarray(rgb_image)
        )
        result = self._landmarker.detect(image)
        if not result.hand_landmarks:
            return None
        return np.array(
            [[p.x, p.y, p.z] for p in result.hand_landmarks[0]], dtype=np.float32
        )

    def features(self, rgb_image):
        """Detect a hand and return (features_63 or None, raw_landmarks or None)."""
        raw = self.detect(rgb_image)
        if raw is None:
            return None, None
        return normalize_landmarks(raw), raw

    def close(self):
        self._landmarker.close()


if __name__ == "__main__":
    # Quick self-test:  python src/hand_detection.py path/to/image.jpg
    import cv2

    if len(sys.argv) < 2:
        sys.exit("Usage: python src/hand_detection.py <image.jpg>")
    img = cv2.cvtColor(cv2.imread(sys.argv[1]), cv2.COLOR_BGR2RGB)
    det = HandDetector()
    feats, _ = det.features(img)
    print("No hand detected" if feats is None else f"Hand found, {len(feats)} features")
    det.close()
