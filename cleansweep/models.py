import datetime
import itertools
from collections import defaultdict
from flask.ext.sqlalchemy import SQLAlchemy
from sqlalchemy.dialects.postgresql import JSON
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

# The place_parents table stores the parent-child relation
# of places. For convenience, we also store a place as parent of it self.
# That makes it easier to run queries over the subtree, including that place.
place_parents = db.Table('place_parents',
    db.Column('parent_id', db.Integer, db.ForeignKey('place.id')),
    db.Column('child_id', db.Integer, db.ForeignKey('place.id'))
)

class Place(db.Model):
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
        order_by='Place.id')

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

    def add_member(self, name, email, phone, voterid=None):
        """Adds a new member.

        The caller is responsible to call db.session.commit().
        """
        member = Member(self, name, email, phone, voterid)
        db.session.add(member)
        return member   

    def add_committee_type(self, place_type, name, description, slug):
        """Adds a new CommitteeType to this place.

        It is caller's responsibility to call db.session.commit().
        """
        c = CommitteeType(
                place=self,
                place_type=place_type,
                name=name,
                description=description,
                slug=slug)
        db.session.add(c)
        return c

    def get_committees(self):
        """Returns all committees at this place.
        """
        q = CommitteeType.query_by_place(self, recursive=True)
        committee_types = q.all()
        def get_committee(type):
            return type.committees.filter_by(place_id=self.id).first() or Committee(self, type)
        return [get_committee(type) for type in committee_types]

    def get_committee(self, slug):
        """Returns a committee with given slug.

        * If there is already a committee with that slug, it will be returned.
        * If there is no committee with that slug, but a committee structure
        is defined here or by a parent, a new committee instance will returned.
        * If neither a committe nor a committee strucutre is found for that
        slug, then None is returned.
        """
        committee_type = CommitteeType.find(self, slug, recursive=True)
        if committee_type:
            c = committee_type.committees.filter_by(place_id=self.id).first()
            if not c:
                c = Committee(self, committee_type)
            return c

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

    def get_mv_requests(self, status='pending', limit=100, offset=0):
        """Returns all the pending MV requests below this place.
        """
        return (MVRequest
                .query
                .filter_by(status=status)
                .filter(
                    MVRequest.place_id==place_parents.c.child_id,
                    place_parents.c.parent_id==self.id)
                .limit(limit)
                .offset(offset)
                .all())

    def get_voters(self, limit=100, offset=0):
        if self.type.short_name == "PB":
            q = VoterInfo.query.filter_by(place_id=self.id)
        else:
            q = (VoterInfo.query.filter(
                    VoterInfo.place_id==place_parents.c.child_id,
                    place_parents.c.parent_id==self.id))
        return q.limit(limit).offset(offset).all()

    def __eq__(self, other):
        return isinstance(other, Place) and self.id == other.id


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

    def __init__(self, place, name, email, phone, voterid):
        self.name = name
        self.email = email
        self.phone = phone
        self.place = place
        self.voterid = voterid

    @staticmethod
    def find(email=None, **kw):
        if email:
            kw['email'] = email
        return Member.query.filter_by(**kw).first()

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

    def get_permissions(self, place):
        """Finds the permissions the user has at given place.

        Every person will have read permission at his own place and the
        permission that he gets by becoming member of one or more committees.
        """
        perms = set()
        if self.place == place or self.place.has_parent(place):
            perms.add("read")

        for cm in self.committees.all():
            committee_place = cm.committee.place
            if committee_place == place or place.has_parent(committee_place):
                perms.update(cm.role.permission.split(","))

        status = MVRequest.get_request_status(self, place)
        if status == 'approved':
            perms.update(["read", "write"])

        return perms

class CommitteeType(db.Model):
    """Specification of a Committee.
    """
    __tablename__ = "committee_type"
    __table_args__ = (db.UniqueConstraint('place_id', 'slug'), {})

    id = db.Column(db.Integer, primary_key=True)

    # id of the place below which this committee can be created.
    place_id = db.Column(db.Integer, db.ForeignKey('place.id'))
    place = db.relationship('Place', backref=db.backref('committee_types', lazy='dynamic'))

    # A committee is always available for a type of places.
    # For example, a state can specify a committee that every ward can have.
    place_type_id = db.Column(db.Integer, db.ForeignKey('place_type.id'))
    place_type = db.relationship('PlaceType', foreign_keys=[place_type_id])

    # name and description of the committee
    name = db.Column(db.Text, nullable=False)
    slug = db.Column(db.Text, nullable=False)
    description = db.Column(db.Text)

    def __init__(self, place, place_type, name, description, slug):
        self.place = place
        self.place_type = place_type
        self.name = name
        self.description = description
        self.slug = slug

    def __repr__(self):
        return "<CommitteeType#{} - {} - {}>".format(self.id, self.place.key, self.name)

    def add_role(self, role_name, multiple, permission):
        """Adds a new role to this CommitteeType.

        The caller must call db.session.commit() explicitly to see these changes.
        """
        role = CommitteeRole(self, role_name, multiple, permission)
        db.session.add(role)

    @staticmethod
    def find(place, slug, recursive=False):
        """Returns CommitteeType defined at given place with given slug.

        If recursive=True, it tries to find the CommitteType at nearest parent,
        but make sures the committee_type matches the place_type.
        """
        q = CommitteeType.query_by_place(place, recursive=recursive).filter_by(slug=slug)
        return q.first()

    @staticmethod
    def query_by_place(place, recursive=True):
        """Returns a query object to query by place.

        If recursive=True, the returned query tries to find the committee_types
        at nearest parent, but make sures the committee_type matches the place_type.
        """
        if recursive:
            parents = [place] + place.parents
            parent_ids = [p.id for p in parents]

            # XXX-Anand
            # Taking the first matching row for now.
            # The right thing is to take the one the is nearest.
            # Will fix that later
            q = CommitteeType.query.filter(CommitteeType.place_id.in_(parent_ids))
            q = q.filter_by(place_type_id=place.type_id)
        else:
            q = CommitteeType.query.filter_by(place_id=place.id)
        return q

    @staticmethod
    def new_from_formdata(place, form):
        """Creates new CommitteeType instance from form data.
        """
        c = CommitteeType(place,
            place_type=PlaceType.get(form.level.data),
            name=form.name.data,
            description=form.description.data,
            slug=form.slug.data)
        db.session.add(c)
        for roledata in form.data['roles']:
            if roledata['name'].strip():
                c.add_role(
                    roledata['name'],
                    roledata['multiple'] == 'yes',
                    roledata['permission'])
        return c

class CommitteeRole(db.Model):
    """Role in a committee.

    A CommitteeType defines all roles that a committee is composed of.
    Right now there can be only one person for a role in the committee.
    Support for specify multiple members and min/max limits is yet to be
    implemented.
    """
    __tablename__ = "committee_role"
    id = db.Column(db.Integer, primary_key=True)
    committee_type_id = db.Column(db.Integer, db.ForeignKey('committee_type.id'))
    committee_type = db.relationship('CommitteeType', backref=db.backref('roles'))

    role = db.Column(db.Text)
    multiple = db.Column(db.Boolean)
    permission = db.Column(db.Text)

    def __init__(self, committee_type, role_name, multiple, permission):
        self.committee_type = committee_type
        self.role = role_name
        self.multiple = multiple
        self.permission = permission

class Committee(db.Model):
    """A real committee.

    The commitee structure is defined by the CommiteeType and a commitee can
    have members for each role defined by the CommitteeType.
    """
    id = db.Column(db.Integer, primary_key=True)

    # A committee is tied to a place
    place_id = db.Column(db.Integer, db.ForeignKey('place.id'))
    place = db.relationship('Place', foreign_keys=place_id,
        backref=db.backref('committees', lazy='dynamic'))

    # And specs of a committe are defined by a CommitteeType
    type_id = db.Column(db.Integer, db.ForeignKey('committee_type.id'))
    type = db.relationship('CommitteeType', foreign_keys=type_id,
        backref=db.backref('committees', lazy='dynamic'))

    def __init__(self, place, type):
        self.place = place
        self.type = type

    def get_members(self):
        """Returns an iterator over role, members for each role in this group.
        """
        d = defaultdict(list)
        for m in self.committee_members:
            d[m.role.id].append(m.member)

        for role in self.type.roles:
            yield role, d[role.id]

    def add_member(self, role, member):
        # TODO: Validate role and member
        # The role should be one of the roles defined in the committee type.
        # The member must be from a place in the subtree of committee's place.
        if not role or not member:
            return

        # Already added
        if CommitteeMember.query.filter_by(committee=self, role=role, member=member).first():
            return
        committee_member = CommitteeMember(self, role, member)
        db.session.add(committee_member)

    def remove_member(self, role, member):
        m = CommitteeMember.query.filter_by(committee_id=self.id, role_id=role.id, member_id=member.id).first()
        if m:
            db.session.delete(m)

class CommitteeMember(db.Model):
    """The members of a committee.
    """
    id = db.Column(db.Integer, primary_key=True)
    committee_id = db.Column(db.Integer, db.ForeignKey("committee.id"))
    committee = db.relationship('Committee', foreign_keys=committee_id,
        backref=db.backref('committee_members'))

    member_id = db.Column(db.Integer, db.ForeignKey('member.id'))
    member = db.relationship('Member', foreign_keys=member_id,
        backref=db.backref('committees', lazy='dynamic'))

    role_id = db.Column(db.Integer, db.ForeignKey('committee_role.id'))
    role = db.relationship('CommitteeRole', foreign_keys=role_id,
        backref=db.backref('members', lazy='dynamic'))

    def __init__(self, committee, role, member):
        self.committee = committee
        self.role = role
        self.member = member

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
        self.place.add_member(self.name, self.email, self.phone, self.voterid)

class VoterInfo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    place_id = db.Column(db.Integer, db.ForeignKey("place.id"), index=True)
    voterid = db.Column(db.Text, nullable=False, index=True)
    place = db.relationship('Place', foreign_keys=place_id)

    @classmethod
    def find(cls, **kw):
        return cls.query.filter_by(**kw).first()

    def get_booth(self):
        return self.place

class MVRequest(db.Model):
    __tablename__ = "mv_request"

    id = db.Column(db.Integer, primary_key=True)
    place_id = db.Column(db.Integer, db.ForeignKey("place.id"), nullable=False, index=True)
    place = db.relationship('Place', foreign_keys=place_id)

    member_id = db.Column(db.Integer, db.ForeignKey("member.id"), nullable=False, index=True)
    member = db.relationship('Member', foreign_keys=member_id)

    timestamp = db.Column(db.DateTime, default=datetime.datetime.now)
    status = db.Column(
        db.Enum("pending", "approved", "rejected", name="mv_request_status"),
        default="pending")

    __table_args__ = (db.UniqueConstraint('place_id', 'member_id'), {})

    def __init__(self, user, place):
        self.member = user
        self.place = place

    @classmethod
    def find(cls, **kw):
        return cls.query.filter_by(**kw).first()

    @classmethod
    def get_request_status(cls, user, place):
        request = cls.find(member_id=user.id, place_id=place.id)
        if request:
            return request.status

    def reject(self):
        self.status = 'rejected'
        db.session.add(self)

    def approve(self):
        self.status = 'approved'
        db.session.add(self)
