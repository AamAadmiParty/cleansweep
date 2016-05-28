from cleansweep.core import voter_lookup
from ...plugin import Plugin
from ...models import db, Member, PendingMember, Place
from flask import (flash, request, session, render_template, redirect, url_for)
from ...core import signals
from ...view_helpers import require_permission
from . import signals, notifications, audits, forms

plugin = Plugin("signups", __name__, template_folder="templates")


def init_app(app):
    plugin.init_app(app)
    plugin.add_sidebar_entry("Signups", endpoint="signups", permission="write",
                             counter_func="get_pending_members_count")

@plugin.route("/account/signup", methods=["GET", "POST"])
def signup():
    userdata = session.get("oauth")

    # is user autheticated?
    if not userdata:
        return render_template("signup.html", userdata=None)

    # Disable member check when _force_signup=true is passed
    if request.args.get('_force_signup') != "true":
        # is already a member?
        user = Member.find(email=userdata['email'])
        if user:
            session['user'] = user.email
            return redirect(url_for("dashboard"))

        # is a pending member?
        pending_member = PendingMember.find(email=userdata['email'])
        if pending_member and not pending_member.status == 'approved':
            return render_template("signup.html", userdata=None, pending_member=pending_member)
    # show the form
    form = forms.SignupForm()
    if request.method == "GET":
        form.name.data = userdata['name']
    if request.method == "POST" and form.validate():
        voter_id = form.voterid.data
        #place_key = form.place.data
        if voter_id:
            voter_data = voter_lookup.get_voter(voter_id)
            place_key = Place.get_pb_key(voter_data['state'], voter_data['ac'], voter_data['pb'])
        else:
            return render_template("signup.html", userdata=userdata, form=form)

        place = Place.find(place_key)
        pending_member = place.add_pending_member(name=form.name.data, email=userdata['email'], phone=form.phone.data,
                                                  voterid=voter_id)
        db.session.commit()
        signals.volunteer_signup.send(pending_member)
        return render_template("signup_complete.html", person=pending_member)
    return render_template("signup.html", userdata=userdata, form=form)


@plugin.route("/<place:place>/signups/<status>", methods=['GET', 'POST'])
@plugin.route("/<place:place>/signups", methods=['GET', 'POST'])
@require_permission("write")
def signups(place, status=None):
    if status not in [None, 'approved', 'rejected']:
        return redirect(url_for(".signups", place=place))
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
                return redirect(url_for(".signups", place=place))
            elif action == 'reject-member':
                pmember.reject()
                db.session.commit()
                signals.volunteer_signup_rejected.send(pmember)
                flash('Successfully rejected {}.'.format(pmember.name))
                return redirect(url_for(".signups", place=place))
    return render_template("signups.html", place=place, status=status)
