"""HTML pages. The frontend developer puts the real pages in templates/ with these names:
landing.html, index.html, auth.html, home.html, studio.html, dictionary.html, insights.html, about.html.
Until a file exists, a small placeholder page is shown so links never break."""
from html import escape
from pathlib import Path

from flask import Blueprint, current_app, redirect, render_template, session

from src.api.routes_auth import current_user

bp = Blueprint("pages", __name__)
PAGES = [("/", "landing.html", False), ("/index", "index.html", False), ("/auth", "auth.html", False), ("/home", "home.html", True),
         ("/studio", "studio.html", True), ("/dictionary", "dictionary.html", True),
         ("/insights", "insights.html", True), ("/about", "about.html", True)]


def make_view(template, needs_login):
    def view():
        if needs_login and current_app.config["REQUIRE_LOGIN"] and "user_id" not in session:
            return redirect("/auth")
        if (Path(current_app.template_folder) / template).exists():
            return render_template(template, user=current_user())
        return (f"<!doctype html><title>SignMark</title><h1>SignMark backend is running</h1>"
                f"<p>The page <code>templates/{escape(template)}</code> has not been added yet.</p>"
                f"<p><a href='/api/health'>API health</a></p>")
    return view


for path, template, needs_login in PAGES:
    bp.add_url_rule(path, endpoint=template.replace(".html", ""), view_func=make_view(template, needs_login))
