"""Register, login, logout and 'who am I'. Login state is a signed session cookie."""
import re
from datetime import date, datetime

from flask import Blueprint, current_app, request, session
from werkzeug.security import check_password_hash, generate_password_hash

from src import auth_db
from src.api.responses import fail, ok

bp = Blueprint("auth", __name__)
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
HASH_METHOD = "pbkdf2:sha256"
DUMMY_HASH = generate_password_hash("not-a-real-password", method=HASH_METHOD)


def public_user(row):
    return {"id": row["id"], "first_name": row["first_name"], "last_name": row["last_name"], "email": row["email"]}


def current_user():
    uid = session.get("user_id")
    return auth_db.user_by_id(current_app.config["DB_PATH"], uid) if uid else None


def validate_registration(body):
    errors = {}
    for field, label in (("first_name", "First name"), ("last_name", "Last name")):
        v = str(body.get(field, "")).strip()
        if not v:
            errors[field] = f"{label} is required."
        elif len(v) > 50:
            errors[field] = f"{label} is too long."
    email = str(body.get("email", "")).strip().lower()
    if not EMAIL_RE.match(email) or len(email) > 254:
        errors["email"] = "Enter a valid email address."
    try:
        dob = datetime.strptime(str(body.get("date_of_birth", "")), "%Y-%m-%d").date()
        if not (date(1900, 1, 1) < dob < date.today()):
            errors["date_of_birth"] = "Date of birth must be a real date in the past."
    except ValueError:
        errors["date_of_birth"] = "Use the format YYYY-MM-DD."
    password = body.get("password")
    if not isinstance(password, str) or not (8 <= len(password) <= 128):
        errors["password"] = "Password must be 8 to 128 characters."
    return errors, email


@bp.post("/api/auth/register")
def register():
    body = request.get_json(silent=True)
    if not isinstance(body, dict):
        return fail("VALIDATION_ERROR", "Send a JSON body.")
    errors, email = validate_registration(body)
    if errors:
        return fail("VALIDATION_ERROR", "Please fix the highlighted fields.", 400, errors)
    uid = auth_db.create_user(current_app.config["DB_PATH"], body["first_name"].strip(), body["last_name"].strip(),
                              email, body["date_of_birth"], generate_password_hash(body["password"], method=HASH_METHOD))
    if uid is None:
        return fail("EMAIL_EXISTS", "An account with this email already exists.", 409)
    session.clear()
    session["user_id"] = uid
    session.permanent = True
    return ok({"user": public_user(auth_db.user_by_id(current_app.config["DB_PATH"], uid))}, 201)


@bp.post("/api/auth/login")
def login():
    body = request.get_json(silent=True)
    if not isinstance(body, dict) or not body.get("email") or not isinstance(body.get("password"), str):
        return fail("VALIDATION_ERROR", "Email and password are required.")
    row = auth_db.user_by_email(current_app.config["DB_PATH"], str(body["email"]).strip().lower())
    good = check_password_hash(row["password_hash"] if row else DUMMY_HASH, body["password"])
    if not row or not good:
        return fail("INVALID_CREDENTIALS", "Wrong email or password.", 401)
    session.clear()
    session["user_id"] = row["id"]
    session.permanent = True
    return ok({"user": public_user(row)})


@bp.post("/api/auth/logout")
def logout():
    session.clear()
    return ok({"message": "Logged out."})


@bp.get("/api/auth/me")
def me():
    row = current_user()
    if row is None:
        return fail("UNAUTHORIZED", "You are not logged in.", 401)
    return ok({"user": public_user(row)})
