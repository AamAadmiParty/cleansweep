from ...core import mailer
from flask import render_template
from . import signals

@signals.add_new_volunteer.connect
def on_add_new_volunteer(volunteer):
    if not volunteer.email or volunteer.email.upper() == "NA":
        return

    message = mailer.Message(to_addr=volunteer.email)
    message.html_body = render_template("emails/add_new_volunteer.html",
        volunteer=volunteer,
        message=message)
    message.send()
