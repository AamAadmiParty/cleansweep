from ..plugin import Plugin
from ..models import db, Member, PendingMember
from flask import (flash, request, session, render_template, redirect, url_for)
from ..core import signals

from . import signals, notifications, audits, forms, signups

plugin = Plugin("signups", __name__, template_folder="templates")


def init_app(app):
    plugin.init_app(app)

@plugin.route("/account/signup", methods=["GET", "POST"])
def signup():
    userdata = session.get("oauth")

    # is user autheticated?
    if not userdata:
        return render_template("signup.html", userdata=None)

    # is already a member?
    user = Member.find(email=userdata['email'])
    if user:
        session['user'] = user.email
        return redirect(url_for("dashboard"))

    # is already a member?
    pending_member = PendingMember.find(email=userdata['email'])
    if pending_member:
        return render_template("signup.html", userdata=None, pending_member=pending_member)

    # show the form
    form = forms.SignupForm()
    if request.method == "GET":
        form.name.data = userdata['name']
    if request.method == "POST" and form.validate():
        person = signups.signup(
            name=form.name.data,
            email=userdata['email'],
            phone=form.phone.data,
            voterid=form.voterid.data,
            place_key=form.place.data)
        db.session.commit()
        signals.volunteer_signup.send(person)
        return render_template("signup_complete.html", person=person)
    return render_template("signup.html", userdata=userdata, form=form)


@plugin.place_view("/signups/<status>", methods=['GET', 'POST'], permission="write")
@plugin.place_view("/signups", methods=['GET', 'POST'], permission="write", sidebar_entry="Signups", endpoint="signups")
def _signups(place, status=None):
    if status not in [None, 'approved', 'rejected']:
        return redirect(url_for(".signups", key=place.key))
    if status is None:
        status = 'pending'

    if request.method == 'POST':
        pmember = PendingMember.find(id=request.form.get('member_id'))
        action = request.form.get('action')
        if pmember and (pmember.place == place or pmember.place.has_parent(place)):
            if action == 'approve-member':
                m = pmember.approve()
                db.session.commit()
                signals.volunteer_signup_approved.send(pmember, member=m)
                flash('Successfully approved {} as a volunteer.'.format(pmember.name))
                return redirect(url_for(".signups", key=place.key))
            elif action == 'reject-member':
                pmember.reject()
                db.session.commit()
                signals.volunteer_signup_rejected.send(pmember)
                flash('Successfully rejected {}.'.format(pmember.name))
                return redirect(url_for(".signups", key=place.key))
    return render_template("signups.html", place=place, status=status)
