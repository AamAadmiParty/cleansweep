"""Views of the admin panel.
"""

from flask import (render_template, abort, url_for, redirect, request, flash)
from ..models import CommitteeType, CommitteeRole, Member, db, PendingMember, MVRequest
from .. import forms
from ..view_helpers import place_view

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

@place_view("/admin/signups/<status>", methods=['GET', 'POST'], permission="write")
@place_view("/admin/signups", methods=['GET', 'POST'], permission="write")
def admin_signups(place, status=None):
    if status not in [None, 'approved', 'rejected']:
        return redirect(url_for("admin_signups", key=place.key))
    if status is None:
        status = 'pending'

    if request.method == 'POST':
        member = PendingMember.find(id=request.form.get('member_id'))
        action = request.form.get('action')
        if member and (member.place == place or member.place.has_parent(place)):
            if action == 'approve-member':
                member.approve()
                db.session.commit()
                flash('Successfully approved {} as a volunteer.'.format(member.name))
                return redirect(url_for("admin_signups", key=place.key))
            elif action == 'reject-member':
                member.reject()
                db.session.commit()
                flash('Successfully rejected {}.'.format(member.name))
                return redirect(url_for("admin_signups", key=place.key))
    return render_template("admin/signups.html", place=place, status=status)

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
