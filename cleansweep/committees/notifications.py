from ..core import mailer
from flask import render_template
from . import signals

@signals.committee_add_member.connect
def on_committee_add_member(committee, member, role):
    if not member or not member.email:
        return

    message = mailer.Message(to_addr=member.email)
    message.html_body = render_template("emails/committee_add_member.html", 
        committee=committee, 
        member=member,
        role=role,
        message=message)
    message.send()

# @signals.committee_remove_member.connect
# def on_committee_remove_member(committee, member, role):
#     if not member.email:
#         return

#     message = mailer.Message(to_addr=member.email)
#     message.html_body = render_template("emails/committee_remove_member.html", committee=committee, member=member, role=role)
#     message.send()

