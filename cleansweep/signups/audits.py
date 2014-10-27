from . import signals
from ..audit import record_audit

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

@signals.volunteer_signup_approved.connect
def on_volunteer_signup_approved(pending_volunteer, member):
    record_audit(
        action="volunteer-signup-approved",
        timestamp=member.created,
        place=pending_volunteer.place,
        data=dict(
            name=pending_volunteer.name,
            email=pending_volunteer.email,
            phone=pending_volunteer.phone,
            voterid=pending_volunteer.voterid
            ))

@signals.volunteer_signup_rejected.connect
def on_volunteer_signup_rejected(pending_volunteer):
    record_audit(
        action="volunteer-signup-rejected",
        timestamp=None,
        place=pending_volunteer.place,
        data=dict(
            name=pending_volunteer.name,
            email=pending_volunteer.email,
            phone=pending_volunteer.phone,
            voterid=pending_volunteer.voterid
            ))
