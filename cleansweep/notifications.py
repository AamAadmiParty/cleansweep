from .core import signals, mailer
from .models import db
from flask import render_template

@signals.login_successful.connect
def on_login_update_ids(user, userdata):
	"""Add Facebook ID to ther user details on login.

	We use the facebook ID and google ID for displaying thumbnails.
	"""
	service = userdata and userdata.get("service", "").lower()
	if service == 'facebook':
		user.add_details('facebook_id', userdata['facebook_id'])
		db.session.commit()

@signals.volunteer_signup.connect
def on_volunteer_signup(volunteer):
	if not volunteer.email:
		return

	message = mailer.Message(to_addr=volunteer.email)
	message.html_body = render_template("emails/volunteer_signup.html", volunteer=volunteer, message=message)
	message.send()
