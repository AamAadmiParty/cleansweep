from flask import (render_template, session, url_for, redirect, request, flash)

from ..app import app
from ..models import db, MVRequest
from .. import forms
from ..view_helpers import place_view
from .. import helpers

@app.route("/")
def home():
    if session.get('user'):
        return redirect(url_for("dashboard"))
    else:
        return render_template("home.html")

@place_view("")
def place(place):
    return render_template("place.html", place=place)

@place_view("/volunteers", permission="view-volunteers")
def volunteers(place):
    return render_template("members.html", place=place)

@place_view("/members/add", methods=["GET", "POST"], permission="write")
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


@place_view("/mv-request", methods=["POST"])
def mv_request(place):
    user = helpers.get_current_user()
    status = MVRequest.get_request_status(user, place)

    if status is None:
        mv = MVRequest(user, place)
        db.session.add(mv)
        db.session.commit()
        flash(
            "Thank you for showing interest to work at this place." +
            " Someone will review your request shortly.",
            category="success")
        return redirect(request.referrer)
    elif status == "pending":
        flash(
            "You've already requested to work at this place." +
            " Someone will review your request shortly.",
            category="warning")
        return redirect(request.referrer)
    else:
        return redirect(request.referrer)