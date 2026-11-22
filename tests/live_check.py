"""Live check of the RUNNING SignMark server (real models, real login session). Standard library only.
1) In one PowerShell window:  python app.py        (wait for 'Running on http://127.0.0.1:5000')
2) In a second window:        python tests/live_check.py
It registers a throw-away test account, uses real sample images from your dataset and prints PASS / FAIL for
every item. It is a wiring check on a handful of images, not an accuracy evaluation."""
import argparse
import base64
import http.cookiejar
import io
import json
import mimetypes
import sys
import time
import urllib.error
import urllib.request
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ap = argparse.ArgumentParser()
ap.add_argument("--base", default="http://127.0.0.1:5000")
BASE = ap.parse_args().base.rstrip("/")
results = []


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *a, **k):
        return None


def make_opener(follow=True):
    jar = http.cookiejar.CookieJar()
    handlers = [urllib.request.HTTPCookieProcessor(jar)] + ([] if follow else [NoRedirect()])
    return urllib.request.build_opener(*handlers)


def call(opener, method, path, json_body=None, files=None, form=None):
    data, headers = None, {}
    if json_body is not None:
        data, headers = json.dumps(json_body).encode(), {"Content-Type": "application/json"}
    elif files is not None:
        boundary = uuid.uuid4().hex
        buf = io.BytesIO()
        for k, v in (form or {}).items():
            buf.write(f"--{boundary}\r\nContent-Disposition: form-data; name=\"{k}\"\r\n\r\n{v}\r\n".encode())
        for k, (name, content) in files.items():
            ctype = mimetypes.guess_type(name)[0] or "application/octet-stream"
            buf.write(f"--{boundary}\r\nContent-Disposition: form-data; name=\"{k}\"; filename=\"{name}\"\r\n"
                      f"Content-Type: {ctype}\r\n\r\n".encode() + content + b"\r\n")
        buf.write(f"--{boundary}--\r\n".encode())
        data, headers = buf.getvalue(), {"Content-Type": f"multipart/form-data; boundary={boundary}"}
    req = urllib.request.Request(BASE + path, data=data, method=method, headers=headers)
    try:
        with opener.open(req, timeout=60) as r:
            return r.status, dict(r.headers), r.read()
    except urllib.error.HTTPError as e:
        return e.code, dict(e.headers), e.read()


def jcall(opener, method, path, **kw):
    status, headers, body = call(opener, method, path, **kw)
    try:
        return status, json.loads(body)
    except ValueError:
        return status, {"_raw": body[:200]}


def check(name, ok, detail=""):
    results.append(ok)
    print(("PASS  " if ok else "FAIL  ") + name + (f"  [{detail}]" if detail else ""))


def samples():
    out = {"alphabet": [], "number": [], "phrase": []}
    for f in sorted((ROOT / "data/raw/asl_alphabet_test/asl_alphabet_test").glob("*_test.jpg"))[:6]:
        out["alphabet"].append((f.stem.split("_")[0], f))
    for d in range(10):
        files = sorted((ROOT / f"data/processed/test/{d}").glob("*"))
        if files and d in (0, 3, 7):
            out["number"].append((str(d), files[0]))
    pdir = ROOT / "data/processed/phrases/test"
    if pdir.is_dir():
        for c in sorted(pdir.iterdir())[:4]:
            files = sorted(c.glob("*"))
            if files:
                out["phrase"].append((c.name, files[0]))
    return out


def main():
    anon, user = make_opener(), make_opener()
    nored = make_opener(follow=False)
    try:
        s, h = jcall(anon, "GET", "/api/health")
    except Exception as e:
        sys.exit(f"Cannot reach {BASE}: {e}\nStart the server first (python app.py).")
    models = h.get("data", {}).get("models", {})
    check("1. server up, all three models loaded", s == 200 and all(m["loaded"] for m in models.values()),
          {k: (v["available"], v["loaded"]) for k, v in models.items()})

    # access control without login
    for method, path in (("GET", "/api/dictionary"), ("GET", "/api/insights"), ("POST", "/api/text-to-sign"),
                         ("POST", "/api/predict/image"), ("POST", "/api/practice/check")):
        s, b = jcall(anon, method, path, json_body={} if method == "POST" else None)
        check(f"2. {method} {path} without login -> 401", s == 401 and b.get("error", {}).get("code") == "UNAUTHORIZED", s)
    s, hdr, _ = call(nored, "GET", "/home")
    check("2. /home without login redirects to /auth", s == 302 and hdr.get("Location") == "/auth", s)

    # registration, session
    email = f"livecheck{int(time.time())}@example.com"
    body = {"first_name": "Live", "last_name": "Check", "email": email, "date_of_birth": "2003-04-05", "password": "live-check-123"}
    s, b = jcall(user, "POST", "/api/auth/register", json_body=body)
    check("3. register new account", s == 201 and b.get("success"), s)
    s, b = jcall(user, "POST", "/api/auth/register", json_body=body)
    check("3. duplicate email rejected (409)", s == 409 and b["error"]["code"] == "EMAIL_EXISTS", s)
    s, b = jcall(anon, "POST", "/api/auth/register", json_body={**body, "email": "bad", "password": "x"})
    check("3. invalid registration rejected (400 with details)", s == 400 and "email" in b["error"].get("details", {}), s)
    s, b = jcall(user, "GET", "/api/auth/me")
    check("4. /api/auth/me returns the logged-in user", s == 200 and b["data"]["user"]["email"] == email, s)
    s, b = jcall(user, "GET", "/api/dictionary")
    check("4. session persists across requests", s == 200, s)
    entries = b.get("data", {}).get("entries", [])

    # dictionary
    cats = {}
    for e in entries:
        cats[e["category"]] = cats.get(e["category"], 0) + 1
    with_media = sum(1 for e in entries if e.get("media_url"))
    check("5. dictionary has entries for all categories", {"Alphabets", "Numbers", "Phrases"} <= set(cats), cats)
    print(f"      entries with a real sign image/video: {with_media} of {len(entries)} (missing ones show a placeholder)")

    # text to sign
    s, b = jcall(user, "POST", "/api/text-to-sign", json_body={"text": "good morning, how are you?"})
    labels = [x["label"] for x in b.get("data", {}).get("signs", [])]
    check("6. text-to-sign: 'good morning, how are you?'", s == 200 and labels == ["good morning", "how are you"], labels)
    s, b = jcall(user, "POST", "/api/text-to-sign", json_body={"text": "You are pretty"})
    d = b.get("data", {})
    check("6. text-to-sign: unsupported words are reported, none invented", d.get("signs") == [] and d.get("unsupported") == ["you", "pretty"], d.get("unsupported"))
    s, b = jcall(user, "POST", "/api/text-to-sign", json_body={"text": "You are pretty", "fingerspell": True})
    check("6. text-to-sign: fingerspelling option", "".join(x["label"] for x in b["data"]["signs"]) == "YOUPRETTY", s)

    # predictions
    smp = samples()
    ok_total = n_total = 0
    for mode, items in smp.items():
        for expected, path in items:
            s, b = jcall(user, "POST", "/api/predict/image", files={"file": (path.name, path.read_bytes())}, form={"mode": mode})
            good = s == 200 and b.get("success")
            n_total += 1
            hit = good and b["data"]["label"] == expected
            ok_total += hit
            print(f"      {mode:9s} expected {expected:>12s} -> {str(b['data']['label']) if good else b}  ({b['data']['status'] if good else s})")
    check("7. image prediction works for all modes (wiring check)", n_total > 0 and ok_total >= max(1, int(0.7 * n_total)), f"{ok_total}/{n_total} matched")
    if smp["alphabet"]:
        label, path = smp["alphabet"][0]
        url = "data:image/jpeg;base64," + base64.b64encode(path.read_bytes()).decode()
        s, b = jcall(user, "POST", "/api/predict/frame", json_body={"image": url, "mode": "alphabet", "session_id": "live"})
        check("7. frame prediction (base64 data URL)", s == 200 and b["data"]["label"] == label, b.get("data", {}).get("label"))
        for exp, want in ((label, "match"), ("Z" if label != "Z" else "A", "mismatch")):
            s, b = jcall(user, "POST", "/api/practice/check", json_body={"image": url, "mode": "alphabet", "expected_label": exp})
            check(f"7. practice check expecting {exp} -> {want}", s == 200 and b["data"]["state"] == want, b.get("data", {}).get("state"))
        s, b = jcall(user, "POST", "/api/practice/check", json_body={"image": url, "mode": "alphabet", "expected_label": "available"})
        check("7. practice check rejects an invalid label (400)", s == 400 and b["error"]["code"] == "VALIDATION_ERROR", s)
    s, b = jcall(user, "GET", "/api/classes")
    check("7. /api/classes lists nested classes", s == 200 and len(b["data"]["alphabet"]["classes"]) == 29, s)
    s, b = jcall(user, "GET", "/api/config")
    check("7. /api/config has frame settings", s == 200 and "green_frames_required" in b["data"], s)

    # insights
    s, b = jcall(user, "GET", "/api/insights")
    d = b.get("data", {})
    check("7. insights available with models and images", s == 200 and d.get("available") and d.get("models") and d.get("images"), len(d.get("images", [])))
    if d.get("images"):
        s, hdr, _ = call(user, "GET", d["images"][0]["url"])
        check("7. chart image is served", s == 200 and "image/png" in hdr.get("Content-Type", ""), s)

    # pages
    missing = []
    for path in ("/", "/index", "/auth", "/home", "/studio", "/dictionary", "/insights", "/about"):
        s, _, page_body = call(user, "GET", path)
        placeholder = b"has not been added yet" in page_body
        if placeholder:
            missing.append(path)
        check(f"8. page {path}", s == 200 and not placeholder, "template missing" if placeholder else s)
    print("      missing templates:", missing or "none")

    # logout and log back in
    jcall(user, "POST", "/api/auth/logout")
    s, _ = jcall(user, "GET", "/api/auth/me")
    check("9. after logout /api/auth/me -> 401", s == 401, s)
    s, _ = jcall(user, "GET", "/api/dictionary")
    check("9. after logout protected endpoints -> 401", s == 401, s)
    s, b = jcall(user, "POST", "/api/auth/login", json_body={"email": email, "password": body["password"]})
    check("9. login with the same account", s == 200, s)
    s, _ = jcall(user, "POST", "/api/auth/login", json_body={"email": email, "password": "wrong-password"})
    check("9. wrong password -> 401", s == 401, s)

    failed = results.count(False)
    print(f"\n{len(results) - failed} of {len(results)} checks passed." + ("  ALL GOOD" if not failed else "  SEE FAIL LINES"))
    sys.exit(1 if failed else 0)


main()
