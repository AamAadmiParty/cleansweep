from . import signals
from ..audit import record_audit

@signals.committee_add_member.connect
def on_committee_add_member(committee, member, role):
    record_audit(
        action="committee.add-member",
        timestamp=None,
        place=committee.place,
        person=member,
        data=dict(
            committee=committee.dict(),
            member=member.dict(),
            role=role.dict()))

@signals.committee_remove_member.connect
def on_committee_remove_member(committee, member, role):
    record_audit(
        action="committee.remove-member",
        timestamp=None,
        place=committee.place,
        person=member,
        data=dict(
            committee=committee.dict(),
            member=member.dict(),
            role=role.dict()))
