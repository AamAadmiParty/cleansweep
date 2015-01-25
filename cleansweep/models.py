import datetime
import itertools
from collections import defaultdict
from flask.ext.sqlalchemy import SQLAlchemy
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.sql.expression import func
from .app import app
import md5

db = SQLAlchemy(app)

class Mixable(object):
    """Magic class to allow adding mixins to the class at run-time.
    """
    @classmethod
    def mixin(cls, mixin):
        """Decorator to add a mixin to the class runtime.
        """
        cls.__bases__ = cls.__bases__ + (mixin,)


class ComparableMixin:
  def __eq__(self, other):
    return not self<other and not other<self
  def __ne__(self, other):
    return self<other or other<self
  def __gt__(self, other):
    return other<self
  def __ge__(self, other):
    return not self<other
  def __le__(self, other):
    return not other<self

class PlaceType(db.Model, ComparableMixin):
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

    def get_subtype(self):
        return PlaceType.query.filter(PlaceType.level > self.level).order_by(PlaceType.level).first()

    def get_subtypes(self):
        return PlaceType.query.filter(PlaceType.level > self.level).order_by(PlaceType.level).all()

    @staticmethod
    def get(short_name):
        """Returns PlaceType object with given short_name.
        """
        return PlaceType.query.filter_by(short_name=short_name).first()

    @staticmethod
    def all():
        return PlaceType.query.order_by(PlaceType.level).all()

    @staticmethod
    def new(name, short_name, level):
        t = PlaceType(name, short_name, level)
        db.sesson.add(t)

    def __lt__(self, other):
        if isinstance(other, PlaceType):
            # Smaller level indicated higher in the hierarchy
            return self.level > other.level
        else:
            return False

# The place_parents table stores the parent-child relation
# of places. For convenience, we also store a place as parent of it self.
# That makes it easier to run queries over the subtree, including that place.
place_parents = db.Table('place_parents',
    db.Column('parent_id', db.Integer, db.ForeignKey('place.id')),
    db.Column('child_id', db.Integer, db.ForeignKey('place.id'))
)

class Place(db.Model, Mixable):
    __tablename__ = "place"

    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.Text, nullable=False)
    name = db.Column(db.Text, nullable=False)
    type_id = db.Column(db.Integer, db.ForeignKey('place_type.id'), nullable=False)
    type = db.relationship('PlaceType', foreign_keys=type_id,
        backref=db.backref('places', lazy='dynamic'))

    # immediate parent
    iparent_id = db.Column(db.Integer, db.ForeignKey('place.id'))
    iparent = db.relationship('Place', remote_side=[id],
        backref=db.backref('child_places', lazy='dynamic'))

    # List of parents
    # Required to list immediate children on the place page
    _parents = db.relationship('Place', 
        secondary=place_parents, 
        primaryjoin=(id==place_parents.c.child_id),
        secondaryjoin=(id==place_parents.c.parent_id),
        backref=db.backref('places', lazy='dynamic', order_by='Place.key'),
        order_by='Place.type_id')

    def __init__(self, key, name, type):
        self.key = key
        self.name = name
        self.type = type
        self._parents = [self]

    def __repr__(self):
        return "Place(%r)" % self.key

    @staticmethod
    def find(key):
        return Place.query.filter_by(key=key).first()

    @staticmethod
    def get_toplevel_places():
        """Returns all places without any parent.
        """
        return Place.query.filter_by(iparent_id=None).all()

    @property 
    def code(self):
        return self.key.split("/")[-1]

    def get_counts(self):
        q = (db.session.query(PlaceType.short_name, db.func.count(Place.id))
            .filter(
                PlaceType.id==Place.type_id,
                place_parents.c.child_id==Place.id,
                place_parents.c.parent_id==self.id)
            .group_by(PlaceType.short_name, PlaceType.level)
            .order_by(PlaceType.level))
        return q.all()

    def get_all_members_query(self):
        q1 = Member.query.filter(
            place_parents.c.child_id==Member.place_id,
            place_parents.c.parent_id==self.id)
        return q1

    def get_member_count(self):
        return self.get_all_members_query().count()

    def get_all_members(self, limit=100, offset=0):
        """Returns all members any this place or any place below this place.
        """
        return self.get_all_members_query().limit(limit).offset(offset).all()

    def get_all_members_iter(self):
        """Returns all members any this place as an iterator.
        """
        limit = 1000
        offset = 0
        size = limit
        while size == limit:
            members = self.get_all_members(limit=limit, offset=offset)
            size = len(members)
            offset = offset + size
            for m in members:
                yield m

    @property
    def parents(self):
        # return all parents except self
        return [p for p in self._parents if self.id != p.id]

    def get_parent(self, type):
        """Returns parent place of given type.
        """
        if isinstance(type, basestring):
            type = PlaceType.get(type)
        try:
            return [p for p in self._parents if p.type == type][0]
        except IndexError:
            return None

    def has_parent(self, parent):
        return parent in self._parents

    def get_places(self, type=None):
        """Returns all places of given type below this place.
        """
        return self._get_places_query(type=type).filter(place_parents.c.child_id != self.id).all()

    def get_places_count(self, type=None):
        return self._get_places_query(type=type).count()

    def _get_places_query(self, type=None):
        q = self.places
        if type:
            q = q.join(PlaceType).filter(PlaceType.id==type.id)
        return q

    def add_place(self, place):
        """Addes a new place as direct child of this place.

        This function takes care of setting parents for the 
        new place.
        """
        # The place is being added as an immediate child of this node.
        place.iparent = self
        # so, it's parents will be self.parents and it self
        place._parents = self._parents + [place]
        db.session.add(place)

    def get_siblings(self):
        parents = sorted(self.parents, key=lambda p: p.type.level)
        if parents:
            return parents[-1].get_places(self.type)
        else:
            # top-level
            return Place.query.filter_by(type=self.type).all()

    def get_child_places_by_type(self):
        """Returns an iterator over type and child-places of that type 
        for all the immediate child places.
        """
        places = self.child_places.all()
        places.sort(key=lambda p: (p.type.level, p.key))
        return itertools.groupby(places, lambda p: p.type)

    def get_all_child_places(self, type):
        q = Place.query.filter(
            place_parents.c.child_id==Place.id,
            place_parents.c.parent_id==self.id)
        if isinstance(type, list):
            q = q.filter(Place.type_id.in_([t.id for t in type]))
        elif type is not None:
            q = q.filter(Place.type_id==type.id)
        q = q.order_by(Place.key)
        return q.all()

    def add_member(self, name, email, phone, voterid=None):
        """Adds a new member.

        The caller is responsible to call db.session.commit().
        """
        member = Member(self, name, email, phone, voterid)
        db.session.add(member)
        return member   


    def get_pending_members(self, status='pending', limit=100, offset=0):
        """Returns all the pending signups below this place.
        """
        return (PendingMember
                .query
                .filter_by(status=status)
                .filter(
                    PendingMember.place_id==place_parents.c.child_id,
                    place_parents.c.parent_id==self.id)
                .limit(limit)
                .offset(offset)
                .all())

    def add_contacts(self, data):
        phones = [row[2].strip() for row in data if row[2] and row[2].strip()]
        emails = [row[1].strip() for row in data if row[1] and row[1].strip()]

        dup_contacts = Contact.query.filter(Contact.phone.in_(phones))
        dup_phones = set(c.phone for c in dup_contacts)

        dup_contacts = Contact.query.filter(Contact.email.in_(emails))
        dup_emails = set(c.email for c in dup_contacts)

        contacts = [
                Contact(self, name, email, phone, voterid)
                for name, email, phone, voterid in data
                if name and name.strip() 
                    and email not in dup_emails
                    and phone not in dup_phones]
        db.session.add_all(contacts)
        return contacts

    def get_contacts(self, limit=100, offset=0):
        return (Contact.query.filter(
                    place_parents.c.child_id==Contact.place_id,
                    place_parents.c.parent_id==self.id)
                .limit(limit).offset(offset).all())

    def get_contact_count(self):
        return Contact.query.filter(
                    place_parents.c.child_id==Contact.place_id,
                    place_parents.c.parent_id==self.id).count()

    def get_contacts_iter(self):
        """Returns all members any this place as an iterator.
        """
        limit = 1000
        offset = 0
        size = limit
        while size == limit:
            contacts = self.get_contacts(limit=limit, offset=offset)
            size = len(contacts)
            offset = offset + size
            for c in contacts:
                yield c

    def __eq__(self, other):
        return isinstance(other, Place) and self.id == other.id

    def get_stats(self, name, limit=100, total=False):
        q = (db.session.query(Stats.date, func.sum(Stats.value).label("value"))
            .filter(
                place_parents.c.parent_id==self.id,
                place_parents.c.child_id==Stats.place_id,
                Stats.name==name)
            .group_by(Stats.date)
            .order_by(Stats.date)
            .limit(limit))
        return q.all()

class Stats(db.Model):
    """Model for storing stats for a place.

    This allows storing a (name, value) or (date, name, number) for a place.
    This is useful for storing values like number of houses visited etc.
    """
    __table_args__ = (db.UniqueConstraint('place_id', 'name', 'date'), {})

    id = db.Column(db.Integer, primary_key=True)

    place_id = db.Column(db.Integer, db.ForeignKey("place.id"), nullable=False)
    date = db.Column(db.Date)
    name = db.Column(db.Text, nullable=False)
    value = db.Column(db.Integer)

class Member(db.Model):
    __tablename__ = "member"
    id = db.Column(db.Integer, primary_key=True)

    place_id = db.Column(db.Integer, db.ForeignKey('place.id'))
    place = db.relationship('Place', backref=db.backref('members', lazy='dynamic'))

    name = db.Column(db.Text, nullable=False)
    email = db.Column(db.Text, unique=True)
    phone = db.Column(db.Text, nullable=False, unique=True)
    voterid = db.Column(db.Text)
    details = db.Column(JSON)
    created = db.Column(db.DateTime, default=datetime.datetime.now)

    def __init__(self, place, name, email, phone, voterid):
        self.name = name
        self.email = email
        self.phone = phone
        self.place = place
        self.voterid = voterid

    def __repr__(self):
        return "<Member:{}>".format(self.email or self.name)

    @staticmethod
    def find(email=None, **kw):
        if email:
            kw['email'] = email
        return Member.query.filter_by(**kw).first()

    def dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "phone": self.phone,
            "voterid": self.voterid
        }

    def add_details(self, name, value):
        """Adds/updates a new name-value pair to member details.
        """
        if self.details is None:
            self.details = {}
        if self.details.get(name) != value:
            self.details[name] = value
            db.session.add(self)

    def get_detail(self, name):
        if self.details:
            return self.details.get(name)

    def get_hash(self):
        key = str(id) + app.config['SECRET_KEY']
        return md5.md5(key).hexdigest()[:7]

    def get_permissions(self, place):
        """Finds the permissions the user has at given place.

        Every person will have read permission at his own place and the
        permission that he gets by becoming member of one or more committees.
        """
        perms = set()
        if self.place == place:
            perms.add("read")
            perms.add("view-volunteers")
        elif self.place.has_parent(place):
            perms.add("read")

        for cm in self.committees.all():
            committee_place = cm.committee.place
            if committee_place == place or place.has_parent(committee_place):
                perms.update(cm.role.permission.split(","))

        from cleansweep.vistaar.models import MVRequest
        status = MVRequest.get_request_status(self, place)
        if status == 'approved':
            perms.update(["read", "write", "view-volunteers"])

        # quick hack to allow committee members to see all the volunteers
        if 'write' in perms:
            perms.add('view-volunteers')

        return perms

    def has_permission(self, place, permission):
        return permission in self.get_permissions(place)

class PendingMember(db.Model):
    __tablename__ = "pending_member"
    id = db.Column(db.Integer, primary_key=True)
    place_id = db.Column(db.Integer, db.ForeignKey("place.id"), nullable=False)
    place = db.relationship('Place', foreign_keys=place_id)

    name = db.Column(db.Text, nullable=False)
    email = db.Column(db.Text, unique=True)
    phone = db.Column(db.Text, unique=True, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.datetime.now)
    voterid = db.Column(db.Text)

    status = db.Column(
        db.Enum("pending", "approved", "rejected", name="pending_member_status"),
        default="pending")

    def __init__(self, place, name, email, phone, voterid):
        self.place = place
        self.name = name
        self.email = email
        self.phone = phone
        self.voterid = voterid

    @classmethod
    def find(cls, **kw):
        return cls.query.filter_by(**kw).first()

    def reject(self):
        self.status = 'rejected'
        db.session.add(self)

    def approve(self):
        self.status = 'approved'
        db.session.add(self)
        return self.place.add_member(self.name, self.email, self.phone, self.voterid)

class Contact(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    place_id = db.Column(db.Integer, db.ForeignKey("place.id"), nullable=False, index=True)
    place = db.relationship('Place', foreign_keys=place_id)
    
    name = db.Column(db.Text, nullable=False)
    email = db.Column(db.Text, index=True)
    phone = db.Column(db.Text, index=True)
    voterid = db.Column(db.Text, index=True)

    def __init__(self, place, name, email, phone, voterid):
        self.place = place
        self.name = name
        self.email = email
        self.phone = phone
        self.voterid = voterid

class Unsubscribe(db.Model):
    """List of people unsubscribes from receiving emails.
    """
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.Text, unique=True)

    def __init__(self, email):
        self.email = email

    @staticmethod
    def contains(email):
        row = Unsubscribe.query.filter_by(email=email).first()
        return bool(row)

    @classmethod
    def unsubscribe(cls, email):
        if cls.contains(email):
            return
        u = Unsubscribe(email)
        db.session.add(u)
        db.session.commit()
