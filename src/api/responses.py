"""One JSON format for every API answer, so the frontend never has to guess."""
from flask import jsonify


def ok(data, status=200):
    return jsonify({"success": True, "data": data}), status


def fail(code, message, status=400, details=None):
    error = {"code": code, "message": message}
    if details:
        error["details"] = details          # e.g. {"email": "Enter a valid email address."}
    return jsonify({"success": False, "error": error}), status
