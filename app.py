"""Start the SignMark backend:  python app.py   (from the project root, venv active)."""
import os

os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "2")   # quieter TensorFlow messages

from src.app_factory import create_app

app = create_app(config={"REQUIRE_LOGIN": True})      # prediction, dictionary, insights need a logged-in user

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False, threaded=True, use_reloader=False)
