from flask import (render_template, session, url_for, redirect, request, flash)

from ..app import app
from ..models import db
from .. import forms
from ..view_helpers import place_view
from .. import helpers

@app.route("/")
def home():
    if session.get('user'):
        return redirect(url_for("dashboard"))
    else:
        # There's nothing on home page yet. Better redirect users straight to the login page.
        return redirect(url_for("login"))
        # return render_template("home.html")

@place_view("")
def place(place):
    return render_template("place.html", place=place)

@place_view("/stats", permission="read")
def stats(place):
    return render_template("admin/stats.html", place=place)

