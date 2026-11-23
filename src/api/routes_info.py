"""Read-only information endpoints: health, classes, config, insights, report images."""
import json
from pathlib import Path

from flask import Blueprint, current_app, send_from_directory

from src.api.responses import fail, ok
from src.model_service import TASKS

bp = Blueprint("info", __name__)
PUBLIC_KEY = {"alphabet": "alphabet", "numbers": "number", "phrases": "phrase"}   # names used in the API contract


@bp.get("/api/health")
def health():
    svc = current_app.extensions["signmark_models"]
    return ok({"status": "ok", "models": svc.status()})


@bp.get("/api/classes")
def classes():
    svc = current_app.extensions["signmark_models"]
    return ok({PUBLIC_KEY[t]: {"available": svc.available(t), "classes": svc.class_names(t)} for t in TASKS})


@bp.get("/api/config")
def config():
    svc = current_app.extensions["signmark_models"]
    c = current_app.config
    return ok({"confidence_threshold": c["DEFAULT_THRESHOLD"],
               "thresholds": {PUBLIC_KEY[t]: svc.threshold(t) for t in TASKS},
               "green_frames_required": c["GREEN_FRAMES"], "red_frames_required": c["RED_FRAMES"],
               "frame_interval_ms": c["FRAME_INTERVAL_MS"], "max_upload_mb": c["MAX_UPLOAD_MB"],
               "frame_input": {"alphabet": "square crop of the guide box", "number": "square crop of the guide box",
                               "phrase": "the full 4:3 camera frame"}})


@bp.get("/api/insights")
def insights():
    reports = Path(current_app.config["REPORTS_DIR"])
    f = reports / "model_insights.json"
    if not f.exists():
        return ok({"available": False, "message": "Evaluation has not been completed yet."})
    data = json.loads(f.read_text(encoding="utf-8"))
    images = [{"title": "Model comparison", "file": "model_comparison.png"},
              {"title": "Per-class F1 (best model per task)", "file": "per_class_f1.png"}]
    for task, info in data.get("tasks", {}).items():
        if info.get("available") and info.get("confusion_matrix_file"):
            images.append({"title": f"{task}: confusion matrix", "file": info["confusion_matrix_file"]})
    models = [{"task": t, "algorithm": m["model"], "accuracy": m["accuracy"], "precision": m["precision_macro"],
               "recall": m["recall_macro"], "f1": m["f1_macro"]}
              for t, info in data.get("tasks", {}).items() if info.get("available") for m in info["models"]]
    images = [dict(i, url=f"/reports/{i['file']}") for i in images if (reports / i["file"]).exists()]
    return ok({"available": True, "generated": data.get("generated"), "models": models,
               "tasks": data.get("tasks"), "images": images, "notes": data.get("limitations", [])})


@bp.get("/reports/<path:name>")
def report_image(name):
    if not name.lower().endswith(".png"):
        return fail("NOT_FOUND", "Only chart images are served here.", 404)
    return send_from_directory(Path(current_app.config["REPORTS_DIR"]), name)
