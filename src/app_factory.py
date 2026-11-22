"""Creates the Flask application. Routes live in src/api/, model code in src/model_service.py."""
import os
import secrets
from datetime import timedelta
from pathlib import Path

from flask import Flask, request, session

from src import auth_db
from src.api import routes_auth, routes_content, routes_info, routes_pages, routes_predict
from src.api.responses import fail
from src.model_service import ModelService

PROJECT_ROOT = Path(__file__).resolve().parents[1]
PROTECTED_PREFIXES = ("/api/predict", "/api/practice", "/api/text-to-sign", "/api/dictionary",
                      "/api/insights", "/reports/")


def load_secret_key():
    """SIGNMARK_SECRET if set, otherwise a random key created once and kept in data/.secret_key."""
    if os.environ.get("SIGNMARK_SECRET"):
        return os.environ["SIGNMARK_SECRET"]
    f = PROJECT_ROOT / "data" / ".secret_key"
    if not f.exists():
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(secrets.token_hex(32))
    return f.read_text().strip()


def create_app(service=None, config=None):
    app = Flask(__name__, template_folder=str(PROJECT_ROOT / "templates"),
                static_folder=str(PROJECT_ROOT / "static"))
    app.config.update(
        SECRET_KEY=None, SESSION_COOKIE_SAMESITE="Lax", SESSION_COOKIE_HTTPONLY=True,
        PERMANENT_SESSION_LIFETIME=timedelta(hours=12),
        REQUIRE_LOGIN=False,        # app.py switches this on for the real server
        DB_PATH=str(PROJECT_ROOT / "data" / "signmark.db"),
        STATIC_SIGNS_DIR=str(PROJECT_ROOT / "static" / "signs"),
        CATALOGUE_FILE=str(PROJECT_ROOT / "data" / "catalogue" / "dictionary.json"),
        MAX_UPLOAD_MB=5, MAX_FRAME_B64=3_000_000, DEFAULT_THRESHOLD=0.80,
        GREEN_FRAMES=5, RED_FRAMES=4, FRAME_INTERVAL_MS=200,
        REPORTS_DIR=str(PROJECT_ROOT / "reports"), PRELOAD_MODELS=True)
    if config:
        app.config.update(config)
    app.config["MAX_CONTENT_LENGTH"] = (app.config["MAX_UPLOAD_MB"] + 1) * 1024 * 1024
    if not app.config["SECRET_KEY"]:
        app.config["SECRET_KEY"] = load_secret_key()
    auth_db.init_db(app.config["DB_PATH"])

    if service is None:
        service = ModelService()
        if app.config["PRELOAD_MODELS"]:
            service.load_all()          # once at start-up, never per request
    app.extensions["signmark_models"] = service

    for module in (routes_info, routes_predict, routes_auth, routes_content, routes_pages):
        app.register_blueprint(module.bp)

    @app.before_request
    def require_login():
        if app.config["REQUIRE_LOGIN"] and request.path.startswith(PROTECTED_PREFIXES) and "user_id" not in session:
            return fail("UNAUTHORIZED", "Please log in first.", 401)

    @app.errorhandler(413)
    def too_large(e):
        return fail("FILE_TOO_LARGE", f"The upload is larger than {app.config['MAX_UPLOAD_MB']} MB.", 413)

    @app.errorhandler(404)
    def not_found(e):
        return fail("NOT_FOUND", "That address does not exist.", 404)

    @app.errorhandler(405)
    def wrong_method(e):
        return fail("METHOD_NOT_ALLOWED", "Wrong HTTP method for this address.", 405)

    @app.errorhandler(500)
    def server_error(e):
        return fail("SERVER_ERROR", "Something went wrong on the server.", 500)

    return app
