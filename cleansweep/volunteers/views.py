from ..plugin import Plugin
from flask import (flash, request, render_template, redirect, url_for, abort, make_response, jsonify)
from ..models import db, Place, Member
from .. import forms
from ..voterlib import voterdb
from . import signals, notifications, audits, stats
import tablib

plugin = Plugin("volunteers", __name__, template_folder="templates")

def init_app(app):
    plugin.init_app(app)


@plugin.place_view("/volunteers", permission="view-volunteers")
def volunteers(place):
    return render_template("volunteers.html", place=place)


@plugin.place_view("/volunteers/add", methods=['GET', 'POST'], permission="write")
def add_volunteer(place):
    form = forms.AddVolunteerForm(place, request.form)
    if request.method == "POST" and form.validate():
        p = Place.find(key=form.booth.data)
        volunteer = p.add_member(
            name=form.name.data,
            email=form.email.data or None,
            phone=form.phone.data or None,
            voterid=form.voterid.data or None)
        db.session.commit()
        signals.add_new_volunteer.send(volunteer)
        flash(u"Added {} as volunteer to {}.".format(form.name.data, p.name))
        return redirect(url_for(".volunteers", key=place.key))
    return render_template("add_volunteer.html", place=place, form=form)


@plugin.place_view("/volunteers/autocomplete", methods=['GET'], permission="write")
def volunteers_autocomplete(place):
    q = request.args.get('q')
    if q:
        matches = place.search_members(q)
        matches = [dict(name=m.name, email=m.email, phone=m.phone, id=m.id) for m in matches]
    else:
        matches = []
    return jsonify({"matches": matches})

@plugin.place_view("/volunteers.xls", permission="write")
def download_volunteer(place):
    def get_location_columns():
        return ['State', 'District', 'Assembly Constituency', 'Ward', 'Booth']

    def get_locations(place):
        """Returns all locations in the hierarchy to identify this location.
        """
        d = place.get_parent_names_by_type()
        return [d.get('STATE', '-'), d.get('DISTRICT', '-'), d.get('AC', '-'), d.get('WARD', '-'), d.get('PB', '-')]

    headers = ['Name', "Phone", 'Email', 'Voter ID'] + get_location_columns()
    data = tablib.Dataset(headers=headers, title="Volunteers")
    for m in place.get_all_members():
        data.append([m.name, m.phone, m.email, m.voterid] + get_locations(m.place))
    response = make_response(data.xls)
    response.headers['content_type'] = 'application/vnd.ms-excel;charset=utf-8'
    response.headers['Content-Disposition'] = "attachment; filename='{0}-volunteers.xls'".format(place.key)
    signals.download_volunteers_list.send(place)
    return response


@plugin.route("/people/<id>-<hash>", methods=["GET", "POST"])
def profile(id, hash):
    m = Member.find(id=id)
    if not m or m.get_hash() != hash:
        abort(404)

    if request.method == "POST":
        action = request.form.get('action')
        if action == 'delete':
            place = m.place
            # TODO: Make sure the member is not part of any committee

            # Delete all audit records.
            # XXX: This is very bad. We should never delete any audit records.
            # this is only added as a quick fix. We should find a better way to handle this.
            from ..audit.models import Audit
            Audit.query.filter_by(person_id=m.id).delete()
            Audit.query.filter_by(user_id=m.id).delete()
            db.session.delete(m)
            db.session.commit()
            signals.delete_volunteer.send(m, place=place)
            flash(u"Deleted {} as volunteer.".format(m.name))
            return redirect(url_for("dashboard"))
    else:
        return render_template("profile.html", person=m)
