"""Audit trail for cleansweep.

Every action that modifies something in cleansweep is recorded for maintaining audit trial.
"""
from ..core import signals
from .. import helpers
from .models import Audit, db
from flask import request

def record_audit(action, place, timestamp, person=None, data=None):
    user = helpers.get_current_user()
    url = request.path
    a = Audit(
        action=action,  # what
        user=user,      # who
        timestamp=timestamp,    # when
        place=place,    # where
        person=person,
        url=url,
        data=data)
    db.session.add(a)
    db.session.commit()


@signals.volunteer_signup.connect
def on_volunteer_signup(pending_volunteer):
    record_audit(
        action="volunteer-signup",
        timestamp=pending_volunteer.timestamp,
        place=pending_volunteer.place,
        data=dict(
            name=pending_volunteer.name,
            email=pending_volunteer.email,
            phone=pending_volunteer.phone,
            voterid=pending_volunteer.voterid
            ))
