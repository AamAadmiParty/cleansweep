from .core import signals, mailer
from .models import db
from flask import render_template
import urllib2
import json

@signals.login_successful.connect
def on_login_update_ids(user, userdata):
	"""Add Facebook ID to ther user details on login.

	We use the facebook ID and google ID for displaying thumbnails.
	"""
	service = userdata and userdata.get("service", "").lower()
	if service == 'facebook':
		user.add_details('facebook_id', userdata['facebook_id'])
		db.session.commit()
	elif service == 'google':
		user.add_details('google_id', userdata['google_id'])
		user.add_details('google_image_url', json.loads(urllib2.urlopen( "https://www.googleapis.com/plus/v1/people/"+userdata['google_id']+"?fields=image&key=AIzaSyCdWe-KtVS8Gd-yBv-1pJQyqbbo_EY1Rs4" ).read())['image']['url'])
		db.session.commit()

