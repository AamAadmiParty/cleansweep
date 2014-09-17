from .core import signals
from .models import db

@signals.login_successful.connect
def on_login_update_ids(user, userdata):
	"""Add Facebook ID to ther user details on login.

	We use the facebook ID and google ID for displaying thumbnails.
	"""
	service = userdata and userdata.get("service", "").lower()
	if service == 'facebook':
		user.add_details('facebook_id', userdata['facebook_id'])
		db.session.commit()
