"""Models to support audit trail.
"""
from ..models import db
from sqlalchemy.dialects.postgresql import JSON
import datetime

class Audit(db.Model):
    """Model for maintaining audit trail.

    Records the following for every action that modifies the system.

    action - name of the action
    user - the current logged in user who did this action
    timestamp - timestamp of when this action is done
    place - on which place this action is done
    person - the person affected by this action
    url - the url if the action was invoked by a web request
    data - additional data required to describe this action as JSON
    """
    id = db.Column(db.Integer, primary_key=True)
    action = db.Column(db.Text)
    user_id = db.Column(db.Integer, db.ForeignKey('member.id'), index=True)
    place_id = db.Column(db.Integer, db.ForeignKey('place.id'), index=True)
    person_id = db.Column(db.Integer, db.ForeignKey('member.id'), index=True)
    timestamp = db.Column(db.DateTime, default=datetime.datetime.now)
    url = db.Column(db.Text)
    data = db.Column(JSON)

    def __init__(self, action, user, place, person, timestamp, url, data):
        self.action = action
        self.user = user
        self.place = place
        self.person = person
        self.timestamp = timestamp
        self.url = url
        self.data = data
