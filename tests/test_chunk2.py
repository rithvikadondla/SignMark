"""Tests for login, access control, dictionary, text-to-sign and pages (fake model service, no TensorFlow).
Run from the project root:  python -m unittest tests.test_chunk2 -v"""
import json
import tempfile
import unittest
from pathlib import Path

from src import auth_db
from src.app_factory import create_app

PHRASES = ["good morning", "how are you", "i need help", "keepsmile", "please", "questions"]


class RichFake:
    names = {"alphabet": list("ABCDEFGHIJKLMNOPQRSTUVWXYZ") + ["del", "nothing", "space"],
             "numbers": [str(d) for d in range(10)], "phrases": PHRASES}

    def available(self, task):
        return True

    def class_names(self, task):
        return self.names[task]

    def threshold(self, task):
        return 0.8

    def status(self):
        return {}


USER = {"first_name": "Asha", "last_name": "Rao", "email": "Asha@Example.com",
        "date_of_birth": "2004-05-17", "password": "correct-horse-1"}


class Chunk2Tests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)
        (self.dir / "signs").mkdir()
        self.app = create_app(service=RichFake(), config={
            "TESTING": True, "REQUIRE_LOGIN": True, "DB_PATH": str(self.dir / "t.db"),
            "SECRET_KEY": "test", "STATIC_SIGNS_DIR": str(self.dir / "signs"),
            "CATALOGUE_FILE": str(self.dir / "dictionary.json"), "REPORTS_DIR": str(self.dir)})
        self.c = self.app.test_client()

    def tearDown(self):
        self.tmp.cleanup()

    def register(self, **over):
        return self.c.post("/api/auth/register", json={**USER, **over})

    # ---- authentication ----
    def test_register_login_logout(self):
        r = self.register()
        self.assertEqual(r.status_code, 201)
        self.assertEqual(r.get_json()["data"]["user"]["email"], "asha@example.com")
        self.assertEqual(self.c.get("/api/auth/me").get_json()["data"]["user"]["first_name"], "Asha")
        self.c.post("/api/auth/logout")
        self.assertEqual(self.c.get("/api/auth/me").status_code, 401)
        bad = self.c.post("/api/auth/login", json={"email": "asha@example.com", "password": "wrong-password"})
        self.assertEqual((bad.status_code, bad.get_json()["error"]["code"]), (401, "INVALID_CREDENTIALS"))
        unknown = self.c.post("/api/auth/login", json={"email": "no@one.com", "password": "whatever123"})
        self.assertEqual(unknown.get_json()["error"]["code"], "INVALID_CREDENTIALS")
        good = self.c.post("/api/auth/login", json={"email": " ASHA@example.com ", "password": USER["password"]})
        self.assertTrue(good.get_json()["success"])
        self.assertEqual(self.c.get("/api/auth/me").status_code, 200)

    def test_password_is_hashed_and_duplicates_rejected(self):
        self.register()
        row = auth_db.user_by_email(str(self.dir / "t.db"), "asha@example.com")
        self.assertNotEqual(row["password_hash"], USER["password"])
        self.assertTrue(row["password_hash"].startswith("pbkdf2:"))
        r = self.register(email="asha@example.com")
        self.assertEqual((r.status_code, r.get_json()["error"]["code"]), (409, "EMAIL_EXISTS"))

    def test_registration_validation(self):
        for over, field in ((({"email": "nope"}), "email"), ({"password": "short"}, "password"),
                            ({"date_of_birth": "2999-01-01"}, "date_of_birth"), ({"date_of_birth": "17/05/2004"}, "date_of_birth"),
                            ({"first_name": " "}, "first_name")):
            r = self.register(**over)
            self.assertEqual(r.status_code, 400)
            self.assertIn(field, r.get_json()["error"]["details"])
        self.assertEqual(self.c.post("/api/auth/register", data="x", content_type="text/plain").status_code, 400)

    # ---- access control ----
    def test_login_required(self):
        self.assertEqual(self.c.get("/api/health").status_code, 200)       # public
        self.assertEqual(self.c.get("/api/classes").status_code, 200)      # public
        for path in ("/api/dictionary", "/api/insights"):
            r = self.c.get(path)
            self.assertEqual((r.status_code, r.get_json()["error"]["code"]), (401, "UNAUTHORIZED"))
        self.assertEqual(self.c.post("/api/text-to-sign", json={"text": "please"}).status_code, 401)
        self.assertEqual(self.c.post("/api/predict/image").status_code, 401)
        self.register()
        self.assertEqual(self.c.get("/api/dictionary").status_code, 200)

    # ---- dictionary ----
    def test_dictionary(self):
        self.register()
        (self.dir / "signs" / "A.jpg").write_bytes(b"x")
        (self.dir / "signs" / "good_morning.mp4").write_bytes(b"x")
        (self.dir / "dictionary.json").write_text(json.dumps([
            {"text": "Thank you", "category": "Polite Expressions", "meaning": "Expression of thanks"},
            {"text": "please", "category": "Polite Expressions"}]))
        e = {x["id"]: x for x in self.c.get("/api/dictionary").get_json()["data"]["entries"]}
        self.assertNotIn("alphabet:del", e)
        self.assertTrue(e["alphabet:A"]["recognisable"])
        self.assertEqual(e["alphabet:A"]["media_url"], "/static/signs/A.jpg")
        self.assertIsNone(e["alphabet:B"]["media_url"])                    # no real picture -> none invented
        self.assertEqual(e["phrase:good morning"]["media_type"], "video")
        self.assertEqual(e["phrase:keepsmile"]["text"], "keep smile")
        self.assertFalse(e["extra:Thank you"]["recognisable"])             # extra word: view only
        self.assertEqual(e["phrase:please"]["category"], "Polite Expressions")

    # ---- text-to-sign ----
    def tts(self, text, **kw):
        self.register() if self.c.get("/api/auth/me").status_code == 401 else None
        return self.c.post("/api/text-to-sign", json={"text": text, **kw}).get_json()["data"]

    def test_text_to_sign_vocabulary(self):
        d = self.tts("Good morning, how are you?")
        self.assertEqual([s["label"] for s in d["signs"]], ["good morning", "how are you"])
        self.assertEqual(d["unsupported"], [])
        d = self.tts("I need help please")
        self.assertEqual([s["label"] for s in d["signs"]], ["i need help", "please"])
        self.assertEqual([s["label"] for s in self.tts("keep smile")["signs"]], ["keepsmile"])
        self.assertEqual([s["label"] for s in self.tts("questions")["signs"]], ["questions"])

    def test_text_to_sign_unsupported_is_reported_not_invented(self):
        d = self.tts("You are pretty")
        self.assertEqual((d["signs"], d["unsupported"], d["dropped"]), ([], ["you", "pretty"], ["are"]))
        d = self.tts("You are pretty", fingerspell=True)
        self.assertEqual("".join(s["label"] for s in d["signs"]), "YOUPRETTY")
        self.assertTrue(all(s["source"] == "fingerspelling" for s in d["signs"]))
        self.assertEqual(d["unsupported"], ["you", "pretty"])              # still listed as unsupported

    def test_text_to_sign_numbers_and_motion_note(self):
        d = self.tts("12")
        self.assertEqual([(s["label"], s["mode"]) for s in d["signs"]], [("1", "number"), ("2", "number")])
        d = self.tts("zoo", fingerspell=True)
        self.assertIn("note", d["signs"][0])                               # Z is a motion sign

    def test_text_to_sign_validation(self):
        self.register()
        for body in ({}, {"text": "  "}, {"text": 5}, {"text": "a" * 201}):
            self.assertEqual(self.c.post("/api/text-to-sign", json=body).status_code, 400)

    # ---- pages ----
    def test_pages(self):
        self.assertEqual(self.c.get("/").status_code, 200)
        r = self.c.get("/home")
        self.assertEqual((r.status_code, r.headers["Location"]), (302, "/auth"))
        self.register()
        self.assertEqual(self.c.get("/home").status_code, 200)             # placeholder until the frontend file exists
        self.assertEqual(self.c.get("/studio").status_code, 200)           # the real page, or a placeholder if the file is missing
        self.assertEqual(self.c.get("/index").status_code, 200)


if __name__ == "__main__":
    unittest.main()
