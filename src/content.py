"""Dictionary and text-to-sign logic (no Flask here, so it is easy to test).

Honesty rules: only signs that the trained models know (A-Z, 0-9 and the phrase classes) are offered.
Words without a known sign are LISTED as unsupported, never invented. Sign pictures/videos are used only if
you put real files in static/signs/ (e.g. static/signs/A.jpg, static/signs/good_morning.mp4)."""
import json
import re
from pathlib import Path

CONTROL = {"del", "nothing", "space"}
DISPLAY = {"keepsmile": "keep smile"}                 # label -> text shown to people
DROP = {"a", "an", "the", "is", "are", "am", "was", "were", "be", "to", "of"}
MOTION_NOTE = "This sign uses motion in ASL; recognition checks a still image only."
MEDIA_EXT = {".gif": "image", ".webp": "image", ".jpg": "image", ".jpeg": "image", ".png": "image",
             ".mp4": "video", ".webm": "video"}


def display_text(label):
    return DISPLAY.get(label, label)


def find_media(signs_dir, label):
    """Return (url, type) for a real file in static/signs/ whose name matches the label, else (None, None).
    Matching ignores upper/lower case (so Windows and Linux behave the same) and the URL uses the
    file's real name, e.g. label 'A' + file 'A.jpg' -> /static/signs/A.jpg."""
    folder = Path(signs_dir)
    if not folder.is_dir():
        return None, None
    files = {p.name.lower(): p.name for p in folder.iterdir() if p.is_file()}
    stem = re.sub(r"\s+", "_", label.lower())
    for ext, kind in MEDIA_EXT.items():
        for key in (stem + ext, label.lower() + ext):
            if key in files:
                return f"/static/signs/{files[key]}", kind
    return None, None


def build_dictionary(service, signs_dir, catalogue_file=None):
    entries, index = [], {}

    def add(kind, label, category, meaning, recognisable=True):
        url, mtype = find_media(signs_dir, label)
        e = {"id": f"{kind}:{label}", "text": display_text(label), "category": category, "meaning": meaning,
             "media_url": url, "media_type": mtype, "recognisable": recognisable}
        entries.append(e)
        index[display_text(label).lower()] = e

    if service.available("alphabet"):
        for c in service.class_names("alphabet"):
            if c not in CONTROL:
                add("alphabet", c, "Alphabets", f"Letter {c}")
    if service.available("numbers"):
        for c in service.class_names("numbers"):
            add("number", c, "Numbers", f"Number {c}")
    if service.available("phrases"):
        for c in service.class_names("phrases"):
            add("phrase", c, "Phrases", display_text(c))
    if catalogue_file and Path(catalogue_file).exists():
        for item in json.loads(Path(catalogue_file).read_text(encoding="utf-8")):
            text = str(item.get("text", "")).strip()
            if not text:
                continue
            e = index.get(text.lower())
            if e is None:       # an extra word/phrase: shown for learning, not recognised by the AI
                e = {"id": f"extra:{text}", "text": text, "category": "Other", "meaning": text,
                     "media_url": None, "media_type": None, "recognisable": False}
                entries.append(e)
            for k in ("category", "meaning", "media_url", "media_type"):
                if item.get(k):
                    e[k] = item[k]
    return entries


def text_to_sign(text, service, signs_dir, fingerspell=False):
    words = re.findall(r"[a-z0-9']+", text.lower())
    phrases = {}
    if service.available("phrases"):
        phrases = {re.sub(r"\s+", "", c.lower()): c for c in service.class_names("phrases")}
    signs, unsupported, dropped = [], [], []

    def sign(label, mode, source):
        task = {"alphabet": "alphabet", "number": "numbers", "phrase": "phrases"}[mode]
        url, mtype = find_media(signs_dir, label)
        s = {"label": label, "display": display_text(label), "mode": mode, "source": source,
             "media_url": url, "media_type": mtype, "checkable": service.available(task)}
        if mode == "alphabet" and label in ("J", "Z"):
            s["note"] = MOTION_NOTE
        signs.append(s)

    def spell(word):
        for ch in word:
            if ch.isdigit() and service.available("numbers"):
                sign(ch, "number", "fingerspelling")
            elif ch.isalpha() and service.available("alphabet"):
                sign(ch.upper(), "alphabet", "fingerspelling")

    i = 0
    while i < len(words):
        hit = None
        for n in range(min(4, len(words) - i), 0, -1):
            key = "".join(words[i:i + n])
            if key in phrases:
                hit = (phrases[key], n)
            elif n == 1 and key.endswith("s") and key[:-1] in phrases:
                hit = (phrases[key[:-1]], 1)
            if hit:
                break
        if hit:
            sign(hit[0], "phrase", "vocabulary")
            i += hit[1]
            continue
        w = words[i]
        i += 1
        if w in DROP:
            dropped.append(w)
        elif w.isdigit():
            if service.available("numbers"):
                spell(w)
            else:
                unsupported.append(w)
        else:
            unsupported.append(w)
            if fingerspell:
                spell(w)
    note = ("Only the signs the trained models know are offered: the phrase signs, letters A-Z and digits 0-9. "
            "Words without a known sign are listed in 'unsupported'; nothing is invented. Small English function "
            "words are listed in 'dropped'. No other grammar rewriting is applied. Numbers are shown digit by digit.")
    if unsupported and not fingerspell:
        note += " Send fingerspell=true to spell unsupported words letter by letter."
    return {"text": text, "words": words, "signs": signs, "unsupported": unsupported,
            "dropped": dropped, "fingerspell": bool(fingerspell), "note": note}
