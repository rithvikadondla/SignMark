"""Prediction endpoints: uploaded image, webcam frame, sign-practice check."""
import base64
import binascii

import cv2
import numpy as np
from flask import Blueprint, current_app, request

from src.api.responses import fail, ok
from src.model_service import normalize_mode

bp = Blueprint("predict", __name__)
ALLOWED_EXT = {".jpg", ".jpeg", ".png"}
PUBLIC_KEY = {"alphabet": "alphabet", "numbers": "number", "phrases": "phrase"}


class ApiError(Exception):
    def __init__(self, code, message, status=400):
        self.code, self.message, self.status = code, message, status


@bp.errorhandler(ApiError)
def handle_api_error(e):
    return fail(e.code, e.message, e.status)


def decode_image(data):
    """bytes -> RGB uint8 array, or ApiError."""
    img = cv2.imdecode(np.frombuffer(data, dtype=np.uint8), cv2.IMREAD_COLOR)
    if img is None or img.shape[0] < 16 or img.shape[1] < 16:
        raise ApiError("BAD_IMAGE", "The file is not a readable image.")
    return cv2.cvtColor(img, cv2.COLOR_BGR2RGB)


def get_task(mode):
    task = normalize_mode(mode)
    if task is None:
        raise ApiError("BAD_MODE", "mode must be 'alphabet', 'number' or 'phrase'.")
    if not current_app.extensions["signmark_models"].available(task):
        raise ApiError("MODEL_NOT_AVAILABLE", f"The {mode} model is not available yet.", 503)
    return task


def frame_from_json(body):
    """Read the base64 image from a JSON body (a data URL or plain base64)."""
    if not isinstance(body, dict) or not isinstance(body.get("image"), str):
        raise ApiError("VALIDATION_ERROR", "JSON body with an 'image' field (base64) is required.")
    text = body["image"].split(",", 1)[-1]
    if len(text) > current_app.config["MAX_FRAME_B64"]:
        raise ApiError("FILE_TOO_LARGE", "The frame is too large. Send a smaller JPEG.", 413)
    try:
        raw = base64.b64decode(text, validate=True)
    except (binascii.Error, ValueError):
        raise ApiError("BAD_IMAGE", "The image is not valid base64.")
    return decode_image(raw)


def run_prediction(task, rgb):
    svc = current_app.extensions["signmark_models"]
    try:
        return svc.predict(task, rgb)
    except LookupError as e:
        raise ApiError("MODEL_NOT_AVAILABLE", str(e), 503)
    except Exception as e:
        raise ApiError("SERVER_ERROR", f"Prediction failed: {e}", 500)


def prediction_payload(task, result):
    return {"mode": PUBLIC_KEY[task], "hand_detected": None, "status": result["status"],
            "label": result["label"], "confidence": result["confidence"], "top3": result["top3"],
            "landmarks": None, "threshold": result["threshold"], "message": result["message"]}


@bp.post("/api/predict/image")
def predict_image():
    file = request.files.get("file")
    if file is None or not file.filename:
        raise ApiError("NO_FILE", "Upload an image in the 'file' field.")
    name = file.filename.lower()
    if not any(name.endswith(ext) for ext in ALLOWED_EXT):
        raise ApiError("BAD_FILE_TYPE", "Only JPG, JPEG and PNG images are accepted.")
    task = get_task(request.form.get("mode"))
    rgb = decode_image(file.read())
    return ok(prediction_payload(task, run_prediction(task, rgb)))


@bp.post("/api/predict/frame")
def predict_frame():
    body = request.get_json(silent=True)
    task = get_task((body or {}).get("mode"))
    rgb = frame_from_json(body)
    return ok(prediction_payload(task, run_prediction(task, rgb)))


@bp.post("/api/practice/check")
def practice_check():
    """One webcam frame vs the expected sign. The FRONTEND counts consecutive frames:
    yellow = not reliable yet, match = expected sign seen, mismatch = a different sign seen."""
    body = request.get_json(silent=True)
    task = get_task((body or {}).get("mode"))
    expected = (body or {}).get("expected_label")
    svc = current_app.extensions["signmark_models"]
    if not isinstance(expected, str) or expected not in svc.class_names(task):
        raise ApiError("VALIDATION_ERROR", "expected_label must be one of the classes for this mode.")
    result = run_prediction(task, frame_from_json(body))
    if result["status"] != "confident":
        state, msg = "yellow", "Adjusting... hold your hand steady in the box."
    elif result["label"] == expected:
        state, msg = "match", "That looks right."
    else:
        state, msg = "mismatch", f"This looks like {result['label']}. Try again."
    return ok({"state": state, "expected_label": expected, "detected_label": result["label"],
               "confidence": result["confidence"], "landmarks": None, "message": msg})
