"""Dictionary and text-to-sign endpoints."""
from flask import Blueprint, current_app, request

from src import content
from src.api.responses import fail, ok

bp = Blueprint("content", __name__)


@bp.get("/api/dictionary")
def dictionary():
    svc = current_app.extensions["signmark_models"]
    c = current_app.config
    return ok({"entries": content.build_dictionary(svc, c["STATIC_SIGNS_DIR"], c["CATALOGUE_FILE"]),
               "note": "recognisable=true means the AI can check this sign; otherwise it is view only."})


@bp.post("/api/text-to-sign")
def text_to_sign():
    body = request.get_json(silent=True)
    text = (body or {}).get("text") if isinstance(body, dict) else None
    if not isinstance(text, str) or not text.strip():
        return fail("VALIDATION_ERROR", "Send JSON like {\"text\": \"good morning\"}.")
    if len(text) > 200:
        return fail("VALIDATION_ERROR", "Please use at most 200 characters.")
    svc = current_app.extensions["signmark_models"]
    return ok(content.text_to_sign(text, svc, current_app.config["STATIC_SIGNS_DIR"],
                                   bool(body.get("fingerspell", False))))
