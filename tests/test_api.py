"""API tests with a FAKE model service (no TensorFlow needed).
Run from the project root:  python -m unittest tests.test_api -v
They check the API behaviour (validation, JSON format, errors, practice states), not model accuracy."""
import base64
import io
import json
import tempfile
import unittest
from pathlib import Path

import cv2
import numpy as np

from src.app_factory import create_app


class FakeService:
    """Stands in for ModelService. 'A' is confident, others follow the pixel brightness."""
    names = {"alphabet": ["A", "B", "nothing"], "numbers": ["0", "1"], "phrases": ["hello", "thanks"]}

    def available(self, task):
        return task != "phrases"

    def class_names(self, task):
        return self.names[task] if self.available(task) else []

    def threshold(self, task):
        return 0.8

    def status(self):
        return {t: {"available": self.available(t), "loaded": True, "error": None} for t in self.names}

    def predict(self, task, rgb):
        mean = float(rgb.mean())
        if mean < 60:      # dark image -> 'nothing' for alphabet
            label, conf = ("nothing" if task == "alphabet" else self.names[task][0]), 0.95
        elif mean < 120:   # medium -> not sure
            label, conf = self.names[task][0], 0.40
        elif mean < 200:
            label, conf = self.names[task][0], 0.95
        else:              # bright -> second class
            label, conf = self.names[task][1], 0.95
        status = "uncertain" if conf < 0.8 else ("no_hand" if label == "nothing" else "confident")
        return {"status": status, "label": label if status == "confident" else None, "confidence": conf,
                "top3": [{"label": label, "confidence": conf}], "threshold": 0.8, "message": "fake"}


def png_bytes(value, size=40):
    ok, buf = cv2.imencode(".png", np.full((size, size, 3), value, dtype=np.uint8))
    return buf.tobytes()


def data_url(value):
    return "data:image/png;base64," + base64.b64encode(png_bytes(value)).decode()


class ApiTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.app = create_app(service=FakeService(), config={"REPORTS_DIR": self.tmp.name, "TESTING": True})
        self.c = self.app.test_client()

    def tearDown(self):
        self.tmp.cleanup()

    def upload(self, data, name="a.png", mode="alphabet"):
        return self.c.post("/api/predict/image", data={"file": (io.BytesIO(data), name), "mode": mode},
                           content_type="multipart/form-data")

    # ---- information ----
    def test_health_classes_config(self):
        self.assertTrue(self.c.get("/api/health").get_json()["success"])
        cl = self.c.get("/api/classes").get_json()["data"]
        self.assertEqual(cl["alphabet"]["classes"], ["A", "B", "nothing"])
        self.assertFalse(cl["phrase"]["available"])
        cfg = self.c.get("/api/config").get_json()["data"]
        self.assertEqual(cfg["green_frames_required"], 5)

    def test_insights_missing_then_present(self):
        d = self.c.get("/api/insights").get_json()["data"]
        self.assertFalse(d["available"])
        Path(self.tmp.name, "model_insights.json").write_text(json.dumps({
            "generated": "now", "limitations": ["x"], "tasks": {"numbers": {"available": True, "confusion_matrix_file": "cm.png",
            "models": [{"model": "cnn", "accuracy": 1.0, "precision_macro": 1.0, "recall_macro": 1.0, "f1_macro": 1.0}]}}}))
        Path(self.tmp.name, "cm.png").write_bytes(png_bytes(10))
        d = self.c.get("/api/insights").get_json()["data"]
        self.assertTrue(d["available"])
        self.assertEqual(d["models"][0]["algorithm"], "cnn")
        self.assertEqual(d["images"][0]["url"], "/reports/cm.png")
        r = self.c.get("/reports/cm.png")
        self.assertEqual(r.status_code, 200)
        r.close()   # release the file handle (removes the ResourceWarning)
        self.assertEqual(self.c.get("/reports/model_insights.json").status_code, 404)

    # ---- image upload ----
    def test_upload_ok_and_errors(self):
        r = self.upload(png_bytes(150)).get_json()
        self.assertTrue(r["success"])
        self.assertEqual((r["data"]["status"], r["data"]["label"], r["data"]["landmarks"]), ("confident", "A", None))
        self.assertEqual(self.upload(png_bytes(90)).get_json()["data"]["status"], "uncertain")
        self.assertEqual(self.upload(png_bytes(10)).get_json()["data"]["status"], "no_hand")
        self.assertEqual(self.upload(b"not an image").get_json()["error"]["code"], "BAD_IMAGE")
        self.assertEqual(self.upload(png_bytes(150), name="a.gif").get_json()["error"]["code"], "BAD_FILE_TYPE")
        self.assertEqual(self.upload(png_bytes(150), mode="cats").get_json()["error"]["code"], "BAD_MODE")
        r = self.upload(png_bytes(150), mode="phrase")
        self.assertEqual((r.status_code, r.get_json()["error"]["code"]), (503, "MODEL_NOT_AVAILABLE"))
        r = self.c.post("/api/predict/image", data={"mode": "alphabet"}, content_type="multipart/form-data")
        self.assertEqual(r.get_json()["error"]["code"], "NO_FILE")

    def test_singular_and_plural_modes(self):
        self.assertTrue(self.upload(png_bytes(150), mode="number").get_json()["success"])
        self.assertTrue(self.upload(png_bytes(150), mode="numbers").get_json()["success"])

    def test_too_large_upload(self):
        self.app.config["MAX_CONTENT_LENGTH"] = 1000
        r = self.upload(png_bytes(150, size=300))
        self.assertEqual((r.status_code, r.get_json()["error"]["code"]), (413, "FILE_TOO_LARGE"))

    # ---- webcam frame ----
    def test_frame(self):
        r = self.c.post("/api/predict/frame", json={"image": data_url(150), "mode": "alphabet", "session_id": "s"})
        self.assertEqual(r.get_json()["data"]["label"], "A")
        r = self.c.post("/api/predict/frame", json={"image": "%%%", "mode": "alphabet"})
        self.assertEqual(r.get_json()["error"]["code"], "BAD_IMAGE")
        r = self.c.post("/api/predict/frame", json={"mode": "alphabet"})
        self.assertEqual(r.get_json()["error"]["code"], "VALIDATION_ERROR")
        r = self.c.post("/api/predict/frame", data="oops", content_type="text/plain")
        self.assertEqual(r.get_json()["error"]["code"], "BAD_MODE")

    # ---- practice ----
    def test_practice_states(self):
        def check(value, expected="A"):
            return self.c.post("/api/practice/check", json={"image": data_url(value), "mode": "alphabet",
                                                             "expected_label": expected}).get_json()
        self.assertEqual(check(150)["data"]["state"], "match")
        self.assertEqual(check(250)["data"]["state"], "mismatch")      # confident but a different sign
        self.assertEqual(check(90)["data"]["state"], "yellow")         # not reliable -> never red
        self.assertEqual(check(10)["data"]["state"], "yellow")         # no hand -> never red
        self.assertEqual(check(150, expected="Z")["error"]["code"], "VALIDATION_ERROR")

    # ---- general errors ----
    def test_json_errors(self):
        r = self.c.get("/api/nothing-here")
        self.assertEqual((r.status_code, r.get_json()["error"]["code"]), (404, "NOT_FOUND"))
        r = self.c.get("/api/predict/image")
        self.assertEqual((r.status_code, r.get_json()["error"]["code"]), (405, "METHOD_NOT_ALLOWED"))


if __name__ == "__main__":
    unittest.main()
