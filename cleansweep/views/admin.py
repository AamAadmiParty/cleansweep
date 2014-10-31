"""Views of the admin panel.
"""

from flask import (render_template, abort, url_for, redirect, request, flash, jsonify)
from ..models import CommitteeType, CommitteeRole, Member, db, PendingMember, Place
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

@place_view("/admin/voters", methods=['GET', 'POST'], permission="write")
def admin_voters(place):
    page = int(request.args.get('page', 1))
    return render_template("admin/voters.html", place=place, page=page)

@place_view("/admin/voters/<voterid>", methods=['GET', 'POST'], permission="write")
def admin_voter_view(place, voterid):
    voter = voterdb.get_voter(voterid)
    if not voter:
        return abort(404)

    if request.method == 'POST':
        flash('This is still work in progress, please try again after couple of days.', category='warning')
    return render_template("admin/voter.html", place=place, voter=voter)


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
