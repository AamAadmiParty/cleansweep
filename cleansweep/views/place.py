from flask import (render_template, session, url_for, redirect, request, flash)

from ..app import app
from ..models import db
from .. import forms
from ..view_helpers import place_view


@app.route("/")
def home():
    if session.get('user'):
        return redirect(url_for("dashboard"))
    else:
        return render_template("home.html")

@place_view("")
def place(place):
    return render_template("place.html", place=place)

@place_view("/members")
def members(place):
    return render_template("members.html", place=place)

@place_view("/members/add", methods=["GET", "POST"])
def addmember(place):
    form = forms.AddMemberForm(request.form)
    if request.method == "POST" and form.validate():
        # voterid is ignored for now
        place.add_member(form.name.data, form.email.data, form.phone.data)
        db.session.commit()
        flash("Successfully added {} as member.".format(form.name.data), category="success")
        return redirect(url_for("members", key=place.key))
    else:
        return render_template("members/add.html", place=place, form=form)
