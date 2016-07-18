import json

from ...plugin import Plugin
from ...core import rbac
from ...models import db, Member, PlaceType, Place
from .models import CommitteeRole, CommitteeType
from flask import (flash, request, Response, make_response, render_template, redirect, url_for, abort, jsonify)
from . import forms
from . import signals, notifications, audits
from ...view_helpers import require_permission
from collections import defaultdict
import tablib

plugin = Plugin("committees", __name__, template_folder="templates")

plugin.define_permission(
    name="committees.view",
    description="Permission to view committees and committee members"
)

plugin.define_permission(
    name="committees.edit",
    description="Permission to edit committees"
)

plugin.define_permission(
    name="committees.view-contact-details",
    description="Permission to view contact details of committee members",
)

def init_app(app):
    plugin.init_app(app)

@rbac.role_provider
def get_user_roles(user):
    """Returns permission of a role.
    """
    if not user:
        return
    committee_member_objects = user.committees.all()
    for cm in committee_member_objects:
        place = cm.committee.place
        yield {
            "place": place.key,
            "role": cm.role.role,
            "role-id": cm.role.id,
            "committee": cm.committee.type.slug
        }

@rbac.permission_provider
def get_role_permission(role):
    """Returns permission of a role.
    """
    if 'role-id' not in role:
        return []
    roleobj = CommitteeRole.query.filter_by(id=role['role-id']).first()
    pgroup = roleobj.get_permission_group()
    return [{"place": role['place'], "permission": p.name} for p in pgroup.permissions]

@plugin.route("/<place:place>/committees")
@require_permission("committees.view")
def committees(place):
    return render_template("committees.html", place=place)

@plugin.route("/<place:place>/committees/explore")
@require_permission("committees.view")
def explore_committees(place):
    committee_types = CommitteeType.find_all(place, all_levels=True)

    d = defaultdict(list)
    for spec in committee_types:
        d[spec.place_type.name].append(spec)

    place_types = [place.type] + place.type.get_subtypes()
    levels = [t.name for t in place_types]

    return render_template("explore-committees.html",
                            place=place,
                            levels = levels,
                            committee_types=d)


def export_committees_as_dataset(committees, title="Committee Members"):
    """Exports the given list of committees to a tablib dataset.
    """
    place_types = PlaceType.all()
    place_levels = [t.name for t in place_types]

    def get_locations(place):
        """Returns all locations in the hierarchy to identify this location.
        """
        d = place.get_parent_names_by_type()
        return [d.get(t.short_name, '-') for t in place_types]

    headers = place_levels + ['Committee Name', 'Role', 'Name', 'E-mail', 'Phone']
    dataset = tablib.Dataset(headers=headers, title=title)
    for c in committees:
        row0 = get_locations(c.place)
        for role, members in c.get_members():
            for m in members:
                row = row0 + [c.type.name, role.role, m.name, m.email, m.phone]
                dataset.append(row)
    return dataset


def export_committees_as_response(committees, title, filename):
    dataset = export_committees_as_dataset(committees, title=title)
    response = Response(dataset.xls, content_type='application/vnd.ms-excel; charset=utf-8')
    response.headers['Content-Disposition'] = "attachment; filename='{0}'".format(filename.encode('utf-8'))
    return response


@plugin.route("/<place:place>/committees/<slug>.xls", methods=["GET"])
@require_permission("committees.view-contact-details")
def download_committee(place, slug):
    committee = place.get_committee(slug)
    if not committee:
        abort(404)

    title = committee.type.name
    filename = u"{}--{}.xls".format(place.key.replace("/", "-"), title.replace(" ", "-"))
    return export_committees_as_response([committee], title=title, filename=filename)

@plugin.route("/<place:place>/committees/<slug>", methods=["GET"])
@require_permission("committees.view")
def view_committee(place, slug):
    committee = place.get_committee(slug)
    if not committee:
        abort(404)
    return render_template("view_committee.html", place=place, committee=committee)


@plugin.route("/<place:place>/committees/<slug>/edit", methods=["GET", "POST"])
@require_permission("committees.edit")
def edit_committee(place, slug):
    committee = place.get_committee(slug)
    if not committee:
        abort(404)

    if request.method == "POST":
        action = request.form.get('action')
        if action == "add":
            role_id = request.form['role']
            person_id = request.form['person-id']
            role = CommitteeRole.query.filter_by(id=role_id).first()
            member = Member.find(id=person_id)
            if member:
                committee.add_member(role, member)
                db.session.commit()
                signals.committee_add_member.send(committee, member=member, role=role)
                flash("{} has been added as {}".format(member.name, role.role))
            else:
                flash("Invalid input", category='error')
        elif action == 'remove':
            role_id = request.form['role']
            member_id = request.form['person-id']
            role = CommitteeRole.query.filter_by(id=role_id).first()
            member = Member.find(id=member_id)
            committee.remove_member(role, member)
            signals.committee_remove_member.send(committee, member=member, role=role)
            db.session.commit()
            flash("{} has been removed as {}".format(member.name, role.role))

    return render_template("edit_committee.html", place=place, committee=committee)

@plugin.route("/admin/committee-structures/at/<level>/new", methods=['GET', 'POST'])
@require_permission("admin.committee-structures.new")
def new_committee_structure(level):
    place = Place.get_toplevel_place()
    place_type = PlaceType.get(level)
    form = forms.NewCommitteeForm(place)
    if request.method == "POST" and form.validate():
        committee_type = CommitteeType.new_from_formdata(place, place_type, form)
        db.session.commit()
        signals.new_committee_structure.send(committee_type)

        flash("Successfully defined new committee {}.".format(form.slug.data), category="success")
        return redirect(committee_type.url_for(".view_committee_structure"))
    else:
        return render_template("new_committee_structure.html", place=place, place_type=place_type, form=form)

@plugin.route("/admin/committee-structures")
@require_permission("admin.committee-structures.view")
def committee_structures():
    place = Place.get_toplevel_place()
    return render_template("committee_structures.html", place=place)


@plugin.route("/admin/committee-structures/at/<level>")
@require_permission("admin.committee-structures.view")
def committee_structures_by_level(level):
    place_type = PlaceType.get(level)
    place = Place.get_toplevel_place()
    return render_template("view_committee_structures_by_level.html", place_type=place_type, place=place)

@plugin.route("/admin/committee-structures/<slug>")
@require_permission("admin.committee-structures.view")
def view_committee_structure(slug):
    place = Place.get_toplevel_place()
    committee_type = CommitteeType.find(place, slug)
    return render_template("view_committee_structure.html", place=place, committee_type=committee_type)

@plugin.route("/admin/committee-structures/<slug>/edit", methods=['GET', 'POST'])
@require_permission("admin.committee-structures.edit")
def edit_committee_structure(slug):
    place = Place.get_toplevel_place()
    form = forms.NewCommitteeForm(place)
    committee_type = CommitteeType.find(place, slug)
    if request.method == "POST" and form.validate():
        d1 = committee_type.dict()
        form.save(committee_type)
        db.session.commit()
        flash("Successfully updated {}.".format(committee_type.name), category="success")
        signals.committee_structure_modified.send(committee_type, old=d1)
        return redirect(committee_type.url_for(".view_committee_structure"))
    else:
        if request.method != 'POST':
            form.load(committee_type)
        return render_template("edit_committee_structure.html", place=place, committee_type=committee_type, form=form)

@plugin.route("/admin/committee-structures/<slug>/dowload-members")
@require_permission("admin.committee-structures.download-members")
def download_members_of_committee_type(slug):
    place = Place.get_toplevel_place()
    committee_type = CommitteeType.find(place, slug)

    # using export_committees_as_dataset for exporting the data
    # instead of using CommitteeType.get_all_members() as the earlier one
    # already takes care of listing all place levels.
    # The latter one is more effient.
    # TODO: switch the implemenatation to use CommitteeType.get_all_members()
    dataset = export_committees_as_dataset(committee_type.committees.all())
    filename = "{}-{}-all-members.xls".format(place.key, slug)

    response = Response(dataset.xls, content_type='application/vnd.ms-excel;charset=utf-8')
    response.headers['Content-Disposition'] = "attachment; filename='{0}'".format(filename)
    return response


@plugin.route("/admin/committee-structures/export", methods=['GET'])
@require_permission("admin.committee-structures.view")
def export_committee_structures():
    response = jsonify(committee_types=CommitteeType.export())
    response.headers['Content-Type'] = 'application/json'
    response.headers['Content-Disposition'] = "attachment;filename=committee_structures.json"
    return response


@plugin.route("/admin/committee-structures/import", methods=['POST'])
@require_permission("admin.committee-structures.import")
def import_committee_structures():
    json_file = request.files['file']
    file_content = json_file.read()
    try:
        committee_types = json.loads(file_content).get('committee_types') or []
        created = CommitteeType.import_committee_types(committee_types)
        db.session.commit()
        flash("Successfully created {0} of {1} committee structures.".format(len(created), len(committee_types)),
              category="success")
    except ValueError:
        flash("An error occurred. Maybe it was an invalid file. Make sure JSON is correct.", category="error")

    return redirect(url_for(".committee_structures"))
