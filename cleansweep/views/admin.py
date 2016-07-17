"""Views of the admin panel.
"""
from flask import (render_template, abort, url_for, redirect, request,
                    make_response, session, flash)
from ..models import Member, db, PendingMember, Place
from .. import forms
from ..app import app
from ..voterlib import voterdb
from ..view_helpers import require_permission
from ..helpers import get_current_user
from ..core import mailer, smslib
from ..core.permissions import get_all_permissions, PermissionGroup
from ..core.divisions import Division
from ..voterlib import voterdb
from ..plugins.audit import record_audit
import json
from collections import defaultdict
import tablib


@app.route("/admin")
@require_permission("siteadmin")
def admin():
    return render_template("admin/index.html")


@app.route("/admin/permission-groups")
@require_permission("siteadmin")
def admin_permission_groups():
    groups = PermissionGroup.all()
    return render_template("admin/permission-groups/index.html", groups=groups)


@app.route("/admin/permission-groups/<key>")
@require_permission("siteadmin")
def admin_view_permission_group(key):
    group = PermissionGroup.find(key)
    if not group:
        abort(404)
    return render_template("admin/permission-groups/view.html", group=group)


@app.route("/admin/permission-groups/<key>/edit", methods=["GET", "POST"])
@require_permission("siteadmin")
def admin_edit_permission_group(key):
    group = PermissionGroup.find(key)
    all_permissions = get_all_permissions()
    if not group:
        abort(404)

    if request.method == "POST":
        # TODO: form validation
        group.update(
            name=request.form.get("name"),
            description=request.form.get("description"),
            permissions=request.form.getlist("permissions"))
        group.save()
        return redirect(url_for("admin_view_permission_group", key=key))
    return render_template("admin/permission-groups/edit.html",
                group=group,
                all_permissions=all_permissions)


@app.route("/admin/permission-groups/_new", methods=["GET", "POST"])
@require_permission("siteadmin")
def admin_new_permission_group():
    group = PermissionGroup.new()
    all_permissions = get_all_permissions()

    if request.method == "POST":
        # TODO: form validation
        group.update(
            name=request.form.get("name"),
            description=request.form.get("description"),
            permissions=request.form.getlist("permissions"))
        group.save()
        return redirect(url_for("admin_view_permission_group", key=group.key))
    return render_template("admin/permission-groups/edit.html",
                group=group,
                all_permissions=all_permissions,
                new=True)


@app.route("/admin/divisions")
@require_permission("siteadmin")
def admin_divisions():
    divisions = Division.all()
    return render_template("admin/divisions/index.html", divisions=divisions)

@app.route("/admin/divisions/_new", methods=["GET", "POST"])
@require_permission("siteadmin")
def admin_new_division():
    division = Division.new()

    if request.method == "POST":
        # TODO: form validation
        division.update(
            name=request.form.get("name"),
            description=request.form.get("description"))
        division.save()
        return redirect(url_for("admin_divisions"))
    return render_template("admin/divisions/edit.html",
                division=division,
                new=True)


@app.route("/admin/divisions/<key>", methods=["GET", "POST"])
@require_permission("siteadmin")
def admin_edit_division(key):
    division = Division.find(key=key)
    if not division:
        abort(404)

    if request.method == "POST":
        # TODO: form validation
        division.update(
            name=request.form.get("name"),
            description=request.form.get("description"))
        division.save()
        return redirect(url_for("admin_divisions"))
    return render_template("admin/divisions/edit.html",
                division=division)


@app.route("/admin/sudo")
@require_permission("siteadmin")
def admin_sudo():
    if not app.config.get('DEBUG'):
        abort(404)
    email = request.args.get('email')
    if Member.find(email=email):
        session['user'] = email
        return redirect("/")
    else:
        flash('Unable to find user with email %r.' % email, category='error')
        return redirect("/")


@app.route("/<place:place>/sendmail", methods=['GET', 'POST'])
@require_permission("write")
def admin_sendmail(place):
    form = forms.SendMailForm(request.form)
    if request.method == "POST" and form.validate():
        if form.people.data == 'volunteers':
            people = place.get_all_members_iter()
        elif form.people.data == 'contacts':
            people = place.get_contacts_iter()
        else:
            people = [get_current_user()]  # self
        subject = form.subject.data
        message = form.message.data
        for p in people:
            if p.email:
                mailer.sendmail_async(p.email, subject, message, message_html=message)
        return render_template("admin/sendmail.html", place=place, form=form, sent=True)
    return render_template("admin/sendmail.html", place=place, form=form, sent=False)

def get_sms_config(place):
    name = "{}_SMS_CONFIG".format(place.key.replace("/", "_"))
    config = app.config.get(name)
    if not config and place.iparent:
        return get_sms_config(place.iparent)
    return config

@app.route("/<place:place>/sms", methods=['GET', 'POST'])
@require_permission("write")
def admin_sms(place):
    config = get_sms_config(place)
    sms_provider = config and smslib.get_sms_provider(**config)
    is_sms_configured = sms_provider is not None

    form = forms.SendSMSForm(request.form)
    if request.method == "POST" and form.validate() and is_sms_configured:
        if form.people.data == 'self':
            people = [get_current_user()]
        elif form.people.data == 'volunteers':
            people = place.get_all_members_iter()
        elif form.people.data == 'contacts':
            people = place.get_contacts_iter()

        message = form.message.data
        phone_numbers = [p.phone for p in people]
        sms_provider.send_sms_async(phone_numbers, message)
        record_audit(
            action="send-sms",
            timestamp=None,
            place=place,
            data=dict(
                group=form.people.data,
                message=message,
                phone_numbers=sms_provider.process_phone_numbers(phone_numbers)))
        db.session.commit()
        return render_template("admin/sms.html", place=place, form=form, sent=True, is_sms_configured=is_sms_configured)
    return render_template("admin/sms.html", place=place, form=form, sent=False, is_sms_configured=is_sms_configured)

@app.route("/<place:place>/admin/contacts", methods=['GET', 'POST'])
@require_permission("write")
def admin_contacts(place):
    return render_template("admin/contacts.html", place=place)

@app.route("/<place:place>/admin/contacts.xls")
@require_permission("write")
def admin_contacts_download(place):
    contacts = place.get_contacts_iter()

    headers = ['Place', 'Name', 'Phone', 'E-mail', 'Voter ID']
    data = tablib.Dataset(headers=headers, title="Contacts")

    for c in contacts:
        data.append([c.place.key, c.name, c.phone, c.email, c.voterid])

    response = make_response(data.xls)
    response.headers['Content-Type'] = 'application/vnd.ms-excel;charset=utf-8'
    response.headers['Content-Disposition'] = "attachment; filename='{0}-contacts.xls'".format(place.key)
    return response

@app.route("/<place:place>/admin/contacts/add", methods=['GET', 'POST'])
@require_permission("write")
def admin_add_contacts(place):
    if request.method == "POST":
        jsontext = request.form['data']
        action = request.form.get('action', 'add-contacts')
        data = json.loads(jsontext)
        if action == 'add-contacts':
            contacts = _load_contacts(place, data)
            flash(u"Successfully imported {} contacts.".format(len(contacts)))
            return redirect(url_for("admin_contacts", place=place))
        elif action == "add-volunteers":
            volunteers = _add_volunteers(place, data)
            flash(u"Successfully imported {} volunteers.".format(len(volunteers)))
            return redirect(url_for("volunteers.volunteers", place=place))
    return render_template("admin/add_contacts.html", place=place)

def _add_volunteers(place, data):
    # columns: name, email, phone, voterid, location
    data = [row for row in data if row[0] and row[0].strip()]
    volunteers = []
    for name, email, phone, voterid, location in data:
        p = Place.find(key=location)
        if not p or not p.has_parent(place):
            continue
        if email and Member.find(email=email):
            continue
        v = p.add_member(
            name=name,
            email=email or None,
            phone=phone or None,
            voterid=voterid or None)
        volunteers.append(v)
    db.session.commit()
    return volunteers

def _load_contacts(place, data):
    # columns: name, email, phone, voterid, location    
    data = [row for row in data if row[0] and row[0].strip()]
    voterids = [row[3] for row in data if row[3] and row[3].strip() and not row[4]]
    voters = voterdb.load_voters(voterids)
    voterdict = dict((v.voterid, v.place) for v in voters)

    placesdict = defaultdict(list)

    # map from row as tuple to place
    rowdict = {}

    for name, email, phone, voterid, location in data:
        p = None
        if location:
            p = Place.find(key=location)
        if not p and voterid:
            p = voterdict.get(voterid)
        if not p:
            p = place
        rowdict[name, email, phone, voterid] = p

    # mapping from place -> [rows]
    placesdict = defaultdict(list)
    for row, p in rowdict.items():
        placesdict[p].append(row)

    contacts = []
    for p, prows in placesdict.items():
        contacts += p.add_contacts(prows)
    db.session.commit()
    return contacts
