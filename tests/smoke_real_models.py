"""Send REAL sample images from your dataset through the real API pipeline and the real models.
Run from the project root (venv active):  python tests/smoke_real_models.py
This is a quick wiring check on a handful of images, NOT an evaluation (the evaluation is in reports/).
It needs the trained models in models/ and takes a little while because TensorFlow loads first."""
import io
import os
import sys
import time
from pathlib import Path

os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "2")
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.app_factory import create_app

app = create_app()
client = app.test_client()
print("model status:", {k: (v["available"], v["loaded"], v["error"]) for k, v in
                        client.get("/api/health").get_json()["data"]["models"].items()})


def samples():
    a = sorted((ROOT / "data/raw/asl_alphabet_test/asl_alphabet_test").glob("*_test.jpg"))
    for f in a[:12]:
        yield "alphabet", f.stem.split("_")[0], f
    for d in range(10):
        files = sorted((ROOT / f"data/processed/test/{d}").glob("*"))
        if files:
            yield "number", str(d), files[0]
    for c in sorted((ROOT / "data/processed/phrases/test").iterdir())[:10]:
        files = sorted(c.glob("*"))
        if files:
            yield "phrase", c.name, files[0]


right = total = 0
for mode, expected, path in samples():
    t0 = time.time()
    r = client.post("/api/predict/image", data={"file": (io.BytesIO(path.read_bytes()), path.name), "mode": mode},
                    content_type="multipart/form-data").get_json()
    ms = round((time.time() - t0) * 1000)
    if not r["success"]:
        print(f"{mode:9s} expected {expected:>12s} -> ERROR {r['error']['code']}: {r['error']['message']}")
        continue
    d = r["data"]
    total += 1
    right += d["label"] == expected
    print(f"{mode:9s} expected {expected:>12s} -> {str(d['label']):>12s} ({d['status']}, {d['confidence']:.3f}) {ms} ms")
print(f"\nsample check: {right}/{total} matched (a wiring test on a few images, not an accuracy measurement)")
