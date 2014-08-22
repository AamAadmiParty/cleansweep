"""Views of the admin panel.
"""

from flask import (render_template, abort, url_for, redirect, request, flash)
from ..app import app
from ..models import CommitteeType, CommitteeRole, Member, Place, db
from .. import forms

@app.route("/<place:key>/admin")
def admin(key):
    place = Place.find(key)
    if not place:
        abort(404)    
    return render_template("admin/index.html", place=place)

@app.route("/<place:key>/admin/committees")
def committees(key):
    place = Place.find(key)
    if not place:
        abort(404)
    return render_template("admin/committees.html", place=place)

@app.route("/<place:key>/admin/committees/<slug>", methods=["GET", "POST"])
def view_committee(key, slug):
    place = Place.find(key)
    if not place:
        abort(404)
    committee = place.get_committee(slug)
    if not committee:
        abort(404)

    if request.method == "POST":
        action = request.form.get('action')
        if action == "add":
            role_id = request.form['role']
            email = request.form['email']
            role = CommitteeRole.query.filter_by(id=role_id).first()
            member = Member.find(email=email)
            committee.add_member(role, member)
            db.session.commit()
            flash("{} has been added as {}".format(email, role.role))
        elif action == 'remove':
            role_id = request.form['role']
            email = request.form['email']
            role = CommitteeRole.query.filter_by(id=role_id).first()
            member = Member.find(email=email)
            committee.remove_member(role, member)
            db.session.commit()
            flash("{} has been removed as {}".format(email, role.role))

    return render_template("admin/view_committee.html", place=place, committee=committee)

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
        return render_template("admin/new_committee_structure.html", place=place, form=form)

@app.route("/<place:key>/admin/committee-structures")
def committee_structures(key):
    place = Place.find(key)
    if not place:
        abort(404)
    return render_template("admin/committee_structures.html", place=place)

@app.route("/<place:key>/admin/committee-structures/<slug>")
def view_committee_structure(key, slug):
    place = Place.find(key)
    if not place:
        abort(404)
    committee_type = CommitteeType.find(place, slug)
    return render_template("admin/view_committee_structure.html", place=place, committee_type=committee_type)

@app.route("/<place:key>/admin/signups")
def admin_signups(key):
    place = Place.find(key)
    if not place:
        abort(404)
    return render_template("admin/signups.html", place=place)
