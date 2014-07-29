"""Views of the admin panel.
"""

from flask import (render_template, abort, url_for, redirect, request, flash)
from ..app import app
from ..models import CommitteeType, Place, db
from .. import forms

@app.route("/<place:key>/admin")
def admin(key):
    place = Place.find(key)
    if not place:
        abort(404)    
    return render_template("admin/index.html", place=place)

@app.route("/<place:key>/admin/committee-structures/new", methods=['GET', 'POST'])
def new_committee_structure(key):
    place = Place.find(key)
    if not place:
        abort(404)
    form = forms.NewCommitteeForm(place)
    if request.method == "POST" and form.validate():
        committee_type = CommitteeType.new_from_formdata(place, form)
        db.session.commit()

        flash("Successfully defined new committee {}.".format(form.slug.data), category="success")
        return redirect(url_for("view_committee_structure", key=place.key, slug=committee_type.slug))
    else:
        print "validation errors", form.errors
        return render_template("admin/new_committee_structure.html", place=place, form=form)

@app.route("/<place:key>/admin/committee-structures/<slug>")
def view_committee_structure(key, slug):
    place = Place.find(key)
    if not place:
        abort(404)
    committee_type = CommitteeType.find(place, slug)
    return render_template("admin/view_committee_structure.html", place=place, committee_type=committee_type)
