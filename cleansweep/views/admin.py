"""Views of the admin panel.
"""

from flask import (render_template, abort, url_for, redirect, request, flash, jsonify)
from ..models import CommitteeType, CommitteeRole, Member, db, PendingMember, Place, MVRequest
from .. import forms
from ..app import app
from ..voterlib import voterdb
from ..view_helpers import place_view
from ..helpers import get_current_user
from ..core import mailer, smslib
from ..voterlib import voterdb
import json
from collections import defaultdict

@place_view("/admin", permission="write")
def admin(place):
    return render_template("admin/index.html", place=place)

@place_view("/admin/committees", permission="write")
def committees(place):
    return render_template("admin/committees.html", place=place)

@place_view("/admin/committees/<slug>", methods=["GET", "POST"], permission="write")
def view_committee(place, slug):
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

@place_view("/admin/committee-structures/new", methods=['GET', 'POST'], permission="write")
def new_committee_structure(place):
    form = forms.NewCommitteeForm(place)
    if request.method == "POST" and form.validate():
        committee_type = CommitteeType.new_from_formdata(place, form)
        db.session.commit()

        flash("Successfully defined new committee {}.".format(form.slug.data), category="success")
        return redirect(url_for("view_committee_structure", key=place.key, slug=committee_type.slug))
    else:
        return render_template("admin/new_committee_structure.html", place=place, form=form)

@place_view("/admin/committee-structures", permission="write")
def committee_structures(place):
    return render_template("admin/committee_structures.html", place=place)

@place_view("/admin/committee-structures/<slug>", permission="write")
def view_committee_structure(place, slug):
    committee_type = CommitteeType.find(place, slug)
    return render_template("admin/view_committee_structure.html", place=place, committee_type=committee_type)

@place_view("/admin/mv-requests/<status>", methods=['GET', 'POST'], permission="write")
@place_view("/admin/mv-requests", methods=['GET', 'POST'], permission="write")
def admin_mv_requests(place, status=None):
    if status not in [None, 'approved', 'rejected']:
        return redirect(url_for("admin_mv_requests", key=place.key))
    if status is None:
        status = 'pending'

    if request.method == 'POST':
        mv_req = MVRequest.find(id=request.form.get('request_id'))
        action = request.form.get('action')
        if mv_req and (mv_req.place == place or mv_req.place.has_parent(place)):
            if action == 'approve-request':
                mv_req.approve()
                db.session.commit()
                flash('Successfully approved {} to work at {}.'.format(mv_req.member.name, mv_req.place.name))
                return redirect(url_for("admin_mv_requests", key=place.key))
            elif action == 'reject-request':
                mv_req.reject()
                db.session.commit()
                flash('Successfully rejected {}.'.format(mv_req.name))
                return redirect(url_for("admin_mv_requests", key=place.key))
    return render_template("admin/mv_requests.html", place=place, status=status)

@place_view("/admin/voters", methods=['GET', 'POST'], permission="write")
def admin_voters(place):
    page = int(request.args.get('page', 1))
    return render_template("admin/voters.html", place=place, page=page)

@place_view("/admin/voters/<voterid>", methods=['GET', 'POST'], permission="write")
def admin_voter_view(place, voterid):
    voter = voterdb.get_voter(voterid)
    if not voter:
        return abort(404)
    return render_template("admin/voter.html", place=place, voter=voter)


@place_view("/admin/add-volunteer", methods=['GET', 'POST'], permission="write")
def admin_add_volunteer(place):
    form = forms.AddVolunteerForm(place, request.form)
    if request.method == "POST" and form.validate():
        if form.voterid.data:
            voterid = form.voterid.data
            voter = voterdb.get_voter(voterid=voterid)
            p = voter.get_place()
        else:
            p = Place.find(key=form.place.data)
        p.add_member(
            name=form.name.data, 
            email=form.email.data,
            phone=form.phone.data,
            voterid=form.voterid.data)
        db.session.commit()
        flash(u"Added {} as volunteer to {}.".format(form.name.data, p.name))
        return redirect(url_for("admin", key=place.key))
    return render_template("admin/add_volunteer.html", place=place, form=form)

@place_view("/admin/sendmail", methods=['GET', 'POST'], permission="write")
def admin_sendmail(place):
    form = forms.SendMailForm(request.form)
    if request.method == "POST" and form.validate():
        if form.people.data == 'self':
            people = [get_current_user()]
        elif form.people.data == 'volunteers':
            people = place.get_all_members_iter()
        elif form.people.data == 'contacts':
            people = place.get_contacts_iter()          
        subject = form.subject.data
        message = form.message.data
        for p in people:
            if p.email:
                mailer.sendmail_async(p.email, subject, message)
        return render_template("admin/sendmail.html", place=place, form=form, sent=True)
    return render_template("admin/sendmail.html", place=place, form=form, sent=False)

@place_view("/admin/sms", methods=['GET', 'POST'], permission="write")
def admin_sms(place):
    form = forms.SendSMSForm(request.form)
    if request.method == "POST" and form.validate():
        if form.people.data == 'self':
            people = [get_current_user()]
        elif form.people.data == 'volunteers':
            people = place.get_all_members_iter()
        elif form.people.data == 'contacts':
            people = place.get_contacts_iter()
        message = form.message.data
        phone_numbers = [p.phone for p in people]
        smslib.send_sms_async(phone_numbers, message)
        return render_template("admin/sms.html", place=place, form=form, sent=True)
    return render_template("admin/sms.html", place=place, form=form, sent=False)

@place_view("/admin/contacts", methods=['GET', 'POST'], permission="write")
def admin_contacts(place):
    return render_template("admin/contacts.html", place=place)

@place_view("/admin/contacts/add", methods=['GET', 'POST'], permission="write")
def admin_add_contacts(place):
    if request.method == "POST":
        jsontext = request.form['data']
        data = json.loads(jsontext)
        contacts = _load_contacts(place, data)
        flash(u"Successfully imported {} contacts.".format(len(contacts)))
        return redirect(url_for("admin_contacts", key=place.key))
    return render_template("admin/add_contacts.html", place=place)

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
