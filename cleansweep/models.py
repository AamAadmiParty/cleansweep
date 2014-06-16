from flask.ext.sqlalchemy import SQLAlchemy
from .app import app

db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(20), unique=True)
    phone = db.Column(db.String(20), unique=True)
    email = db.Column(db.String(120), unique=True)
    place_id = db.Column(db.Integer, db.ForeignKey('place.id'))
    place = db.relationship('Place',
        backref=db.backref('members', lazy='dynamic'))

    def __init__(self, name, phone, email, place=None):
        self.name = name
        self.phone = phone
        self.email = email
        self.place = place

    def __repr__(self):
        return '<User %r>' % self.username

class PlaceType(db.Model):
    """There are different types of places in the hierarchy like
    country, state, region etc. This table captures that.
    """
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Text, nullable=False)
    short_name = db.Column(db.Text)

    # number to indicate level of the type. For example:
    # 10 for country
    # 20 for state
    # 30 for region
    # etc.
    level = db.Column(db.Integer, nullable=False)

    def __init__(self, name, short_name, level):
        self.name = name
        self.short_name = short_name
        self.level = level

class Place(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.Text, nullable=False)
    name = db.Column(db.Text, nullable=False)
    type_id = db.Column(db.Integer, db.ForeignKey('place_type.id'))

    def add_member(self, member):
        member.place = self
        db.session.add(member)
        db.session.add(self)


