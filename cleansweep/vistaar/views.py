from ..plugin import Plugin
from .models import db, MVRequest
from flask import (flash, request, render_template, redirect, url_for)

from . import signals, notifications, audits

plugin = Plugin("vistaar", __name__, template_folder="templates")

def init_app(app):
    plugin.init_app(app)

@plugin.place_view("/mv-request", methods=["POST"])
def mv_request(place):
    user = helpers.get_current_user()
    status = MVRequest.get_request_status(user, place)

    if status is None:
        mv = MVRequest(user, place)
        db.session.add(mv)
        db.session.commit()
        flash(
            "Thank you for showing interest to work at this place." +
            " Someone will review your request shortly.",
            category="success")
        return redirect(request.referrer)
    elif status == "pending":
        flash(
            "You've already requested to work at this place." +
            " Someone will review your request shortly.",
            category="warning")
        return redirect(request.referrer)
    else:
        return redirect(request.referrer)

@plugin.place_view("/mv-requests/<status>", methods=['GET', 'POST'], permission="write")
@plugin.place_view("/mv-requests", methods=['GET', 'POST'], permission="write")
def admin_mv_requests(place, status=None):
    if status not in [None, 'approved', 'rejected']:
        return redirect(url_for(".admin_mv_requests", key=place.key))
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
                return redirect(url_for(".admin_mv_requests", key=place.key))
            elif action == 'reject-request':
                mv_req.reject()
                db.session.commit()
                flash('Successfully rejected {}.'.format(mv_req.name))
                return redirect(url_for(".admin_mv_requests", key=place.key))
    return render_template("mv_requests.html", place=place, status=status)

