from flask.ext.paginate import Pagination
from ...plugin import Plugin
from flask import (flash, request, render_template, redirect, url_for, abort, make_response, jsonify)
from ...models import db, Place, Member, PendingMember
from ... import helpers as h
from ... import forms
from ...voterlib import voterdb
from . import signals, notifications, audits, stats
from ..audit.models import Audit
from ...view_helpers import require_permission

import tablib

plugin = Plugin("volunteers", __name__, template_folder="templates")

plugin.define_permission(
    name='volunteers.view',
    description='Permission to view volunteers at a place'
)

plugin.define_permission(
    name='volunteers.edit',
    description='Permission to edit details of a volunteer'
)

plugin.define_permission(
    name='volunteers.add',
    description='Permission to add new volunteers'
)

plugin.define_permission(
    name='volunteers.delete',
    description='Permission to delete a volunteer'
)

plugin.define_permission(
    name='volunteers.view-contact-details',
    description='Permission to view contact details of volunteers',
)

plugin.define_permission(
    name='volunteers.download',
    description='Permission to download volunteer details',
)

plugin.define_permission(
    name='volunteers.bulk-import',
    description='Permission to bulk import volunteers',
)

# legacy permissions - defind here temporarily to fix the issues with production
plugin.define_permission(
    name='read',
    description='Legacy Permission to read/view everything at a place'
)

plugin.define_permission(
    name='write',
    description='Legacy Permission to modify everything at a place'
)




def init_app(app):
    plugin.init_app(app)

@plugin.route("/<place:place>/volunteers", methods = ['GET', 'POST'])
@require_permission("volunteers.view")
def volunteers(place):
    page = h.safeint(request.args.get('page', 1), default=1, minvalue=1)
    total_count = place.get_member_count()
    limit = 50
    search_query = request.args.get("q")
    if search_query is None:
        pagination = Pagination(total=total_count, page=page, per_page=limit,
                                bs_version=3, prev_label="&laquo; Prev", next_label="Next &raquo;")
        volunteers_per_page = place.get_all_members(limit=limit, offset=(page - 1) * limit)
    else:
        pagination = None  # It will not exceed the per page limit so no point of having pagination
        volunteers_per_page = place.search_all_members(search_query, limit)
    return render_template("volunteers.html", place=place, pagination=pagination, volunteers=volunteers_per_page,
                           search_query=search_query, limit=limit)


@plugin.route("/<place:place>/volunteers/add", methods=['GET', 'POST'])
@require_permission("volunteers.add")
def add_volunteer(place):
    form = forms.AddVolunteerForm(place, request.form)
    if request.method == "POST" and form.validate():
        # Find the place from voterid if is present
        if form.voterid.data:
            p = form.get_voterid_place()
        p = p or Place.find(key=form.booth.data)

        details = {"added-by": h.get_current_user().email}
        volunteer = p.add_member(
            name=form.name.data,
            email=form.email.data or None,
            phone=form.phone.data or None,
            voterid=form.voterid.data or None, details=details)
        db.session.commit()
        signals.add_new_volunteer.send(volunteer)
        flash(u"Added {} as volunteer to {}.".format(form.name.data, p.name))
        return redirect(url_for(".volunteers", place=place))
    force_add = request.args.get("force") == 'True'
    return render_template("add_volunteer.html", place=place, form=form, force_add=force_add)

@plugin.route("/api/<place:place>/volunteers/add", methods=['POST'])
@require_permission("volunteers.add")
def api_add_volunteer(place):
    data = request.json
    form = forms.BaseAddVolunteerForm(data, csrf_enabled=False)
    if not form.validate():
        return jsonify({"status": "failed", "errors": form.errors}), 400

    volunteer = place.add_member(
        name=data['name'],
        email=data['email'],
        phone=data['phone'],
        voterid=data.get('voterid'))
    db.session.commit()
    signals.add_new_volunteer.send(volunteer)

    return jsonify({
        "status": "ok",
        "message": "Added new volunteer successfully",
        "volunteer": volunteer.dict()
    })


@plugin.route("/<place:place>/volunteers/autocomplete", methods=['GET'])
@require_permission("volunteers.view")
def volunteers_autocomplete(place):
    q = request.args.get('q')
    if q:
        matches = place.search_members(q)
        matches = [dict(name=m.name, email=m.email, phone=m.phone, id=m.id) for m in matches]
    else:
        matches = []
    return jsonify({"matches": matches})

@plugin.route("/<place:place>/volunteers.xls")
@require_permission("volunteers.download")
def download_volunteer(place):
    def get_location_columns():
        return ['State', 'District', 'Assembly Constituency', 'Ward', 'Booth']

    def get_locations(place):
        """Returns all locations in the hierarchy to identify this location.
        """
        d = parents.get(place.id) or {}
        return [d.get('STATE', '-'), d.get('DISTRICT', '-'), d.get('AC', '-'), d.get('WARD', '-'), d.get('PB', '-')]

    members = place.get_all_members(limit=10000)
    parents = Place.bulkload_parent_names([m.place_id for m in members])

    headers = ['Name', "Phone", 'Email', 'Voter ID'] + get_location_columns()
    data = tablib.Dataset(headers=headers, title="Volunteers")
    for m in members:
        data.append([m.name, m.phone, m.email, m.voterid] + get_locations(m.place))
    response = make_response(data.xls)
    response.headers['Content-Type'] = 'application/vnd.ms-excel;charset=utf-8'
    response.headers['Content-Disposition'] = "attachment; filename='{0}-volunteers.xls'".format(place.key)
    signals.download_volunteers_list.send(place)
    return response


@plugin.route("/people/<id>-<hash>", methods=["GET", "POST"])
def profile(id, hash):
    m = Member.find(id=id)
    if not m or m.get_hash() != hash:
        abort(404)

    if not h.has_permission('volunteers.view', m.place):
        return render_template("permission_denied.html")

    if request.method == "POST":
        action = request.form.get('action')
        if action == 'delete':
            pending_member = PendingMember.find(email=m.email)
            place = m.place
            # TODO: Make sure the member is not part of any committee

            # Delete all audit records.
            # XXX: This is very bad. We should never delete any audit records.
            # this is only added as a quick fix. We should find a better way to handle this.
            Audit.query.filter_by(person_id=m.id).delete()
            Audit.query.filter_by(user_id=m.id).delete()
            if pending_member is not None:
                db.session.delete(pending_member)
            db.session.delete(m)
            db.session.commit()
            signals.delete_volunteer.send(m, place=place)
            flash(u"Deleted {} as volunteer.".format(m.name))
            return redirect(url_for("dashboard"))
    else:
        debug = request.args.get("debug") == "true"
        return render_template("profile.html", person=m, debug=debug)

@plugin.route("/people/<id>-<hash>/edit", methods=["GET", "POST"])
@require_permission("volunteers.edit")
def edit_profile(id, hash):
    m = Member.find(id=id)
    if not m or m.get_hash() != hash:
        abort(404)

    if request.method == "POST":
        action = request.form.get('action')
        if action == 'update':
            name=request.form.get('name'),
            email=request.form.get('email'),
            phone=request.form.get('phone'),
            m.name = name
            m.email = email
            m.phone = phone
            db.session.add(m)
            db.session.commit()
            flash(u"Updated {} as volunteer.".format(m.name))
            return redirect(url_for('.profile', id=id, hash=hash))
    else:
        debug = request.args.get("debug") == "true"
        return render_template("edit_profile.html", person=m, debug=debug)
