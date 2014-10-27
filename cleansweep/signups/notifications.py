from ..core import mailer
from flask import render_template

@signals.volunteer_signup.connect
def on_volunteer_signup(volunteer):
	if not volunteer.email:
		return

	message = mailer.Message(to_addr=volunteer.email)
	message.html_body = render_template("emails/volunteer_signup.html", volunteer=volunteer, message=message)
	message.send()

@signals.volunteer_signup_approved.connect
def on_volunteer_signup(volunteer):
	if not volunteer.email:
		return

	message = mailer.Message(to_addr=volunteer.email)
	message.html_body = render_template("emails/volunteer_signup_approved.html", volunteer=volunteer, message=message)
	message.send()

