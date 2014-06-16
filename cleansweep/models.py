from flask.ext.sqlalchemy import SQLAlchemy
from .app import app

db = SQLAlchemy(app)

class PlaceType(db.Model):
    """There are different types of places in the hierarchy like
    country, state, region etc. This table captures that.
    """
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Text, nullable=False)
    short_name = db.Column(db.Text, nullable=False, unique=True)

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

    def __repr__(self):
        return '<%s>' % self.short_name

    @staticmethod
    def get(short_name):
        """Returns PlaceType object with given short_name.
        """
        return PlaceType.query.filter_by(short_name=short_name).first()

    @staticmethod
    def new(name, short_name, level):
        t = PlaceType(name, short_name, level)
        db.sesson.add(t)

place_parents = db.Table('place_parents',
    db.Column('parent_id', db.Integer, db.ForeignKey('place.id')),
    db.Column('child_id', db.Integer, db.ForeignKey('place.id'))
)

class Place(db.Model):
    __table_name__ = "place"
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.Text, nullable=False)
    name = db.Column(db.Text, nullable=False)
    type_id = db.Column(db.Integer, db.ForeignKey('place_type.id'))
    type = db.relationship('PlaceType',
        backref=db.backref('places', lazy='dynamic'))

    # List of parents
    parents = db.relationship('Place', 
        secondary=place_parents, 
        primaryjoin=(id==place_parents.c.child_id),
        secondaryjoin=(id==place_parents.c.parent_id),
        backref=db.backref('places', lazy='dynamic', order_by='Place.key'))

    def __init__(self, key, name, type):
        self.key = key
        self.name = name
        self.type = type

    def __repr__(self):
        return "Place(%r)" % self.key

    @staticmethod
    def find(key):
        return Place.query.filter_by(key=key).first()

    def get_parent(self, type):
        """Returns parent place of given type.
        """
        try:
            return [p for p in self.parents if p.type == type][0]
        except IndexError:
            return None

    def get_places(self, type=None):
        """Returns all places of given type below this place.
        """
        return self._get_places_query(type=type).all()

    def get_places_count(self, type=None):
        return self._get_places_query(type=type).count()

    def _get_places_query(self, type=None):
        q = self.places;
        if type:
            q = q.join(PlaceType).filter(PlaceType.id==type.id)
        return q

    def add_place(self, place):
        """Addes a new place as direct child of this place.

        This function takes care of setting parents for the 
        new place.
        """
        place.parents = self.parents + [self]
        db.session.add(place)

