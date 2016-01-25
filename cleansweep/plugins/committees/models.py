"""Models of committee related tables.
"""
from sqlalchemy import select, func
from ...models import db, Place, place_parents, PlaceType, Member, Place
from ...core.permissions import PermissionGroup
from collections import defaultdict
from flask import url_for

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

    def dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "slug": self.slug,
            "description": self.description,
            "place_key": self.place.key,
            "roles": [role.dict() for role in self.roles]
        }

    def __repr__(self):
        return "<CommitteeType#{} - {} - {}>".format(self.id, self.place.key, self.name)

    def add_role(self, role_name, multiple, permission):
        """Adds a new role to this CommitteeType.

        The caller must call db.session.commit() explicitly to see these changes.
        """
        role = CommitteeRole(self, role_name, multiple, permission)
        db.session.add(role)

    def get_role(self, role_name):
        for role in self.roles:
            if role.role == role_name:
                return role

    @staticmethod
    def find_all(place, all_levels=False):
        """Returns all CommitteeTypes defined for all levels at this place.

        If all_levels is True, also includes all CommitteeType and below.
        """
        q = CommitteeType.query_by_place(place, recursive=True, all_levels=all_levels)
        return q.all()

    @staticmethod
    def find(place, slug, level=None, recursive=False):
        """Returns CommitteeType defined at given place with given slug.

        If recursive=True, it tries to find the CommitteType at nearest parent,
        but make sures the committee_type matches the place_type.
        """
        q = CommitteeType.query_by_place(place, recursive=recursive).filter_by(slug=slug)
        if level:
            place_type = PlaceType.get(level)
            q = q.filter_by(place_type=place_type)
        return q.first()

    @staticmethod
    def query_by_place(place, recursive=True, all_levels=False):
        """Returns a query object to query by place.

        If recursive=True, the returned query tries to find the committee_types
        at nearest parent, but make sures the committee_type matches the place_type.
        """
        if recursive:
            parent_ids = [p.id for p in place._parents]

            # XXX-Anand
            # Taking the first matching row for now.
            # The right thing is to take the one the is nearest.
            # Will fix that later
            q = CommitteeType.query.filter(CommitteeType.place_id.in_(parent_ids))
            if all_levels:
                print "all_levels", all_levels
                place_types = [place.type] + place.type.get_subtypes()
                place_type_ids = [t.id for t in place_types]
                print place_types
                q = q.filter(CommitteeType.place_type_id.in_(place_type_ids))
            else:
                q = q.filter_by(place_type_id=place.type_id)
        else:
            q = CommitteeType.query.filter_by(place_id=place.id)
        return q

    @staticmethod
    def new_from_formdata(place, place_type, form):
        """Creates new CommitteeType instance from form data.
        """
        c = CommitteeType(place,
            place_type=place_type,
            name=form.name.data,
            description=form.description.data,
            slug=form.slug.data)
        db.session.add(c)
        for roledata in form.data['roles']:
            if roledata.get('name') and roledata['name'].strip():
                c.add_role(
                    roledata['name'],
                    roledata['multiple'] == 'yes',
                    roledata['permission'])
        return c

    def url_for(self, endpoint):
        return url_for(endpoint, place=self.place, slug=self.slug)

    def get_level(self):
        return self.place_type.short_name

    def get_stats(self, parent_place=None):
        """Returns a dictionary containing various stats about this committee type.

        If parent_place is specified, the stats will be limited
        to all places at and below that place.

        The stats include the following keys:

            num_roles - The number of available roles in this committee type
            committees_defined - The total number of committees of this type defined
            total_members - Total number of members in all committees of this type
            total_places - Total number of places that can have this committee.
        """
        place = parent_place or self.place
        num_roles = len(self.roles)
        committees_defined = self.committees.count()
        total_members = self._get_all_member_count(place)
        total_places = dict(place.get_counts())[self.place_type.short_name]
        return {
            "num_roles": num_roles,
            "committees_defined": committees_defined,
            "total_members": total_members,
            "total_places": total_places
        }

    def _get_all_member_count(self, place):
        q = self._get_members_query(place)
        q = q.with_only_columns([func.count()])
        row = db.engine.execute(q).fetchone()
        return row[0]

    def _get_members_query(self, place):
        columns = [Place.key, Place.name, CommitteeType.name, CommitteeRole.role, Member.name, Member.email, Member.phone]
        where = []
        tables = [Place, ]
        q = select(columns)
        q = (q
            .where(place_parents.c.child_id==Place.id)
            .where(place_parents.c.parent_id==place.id)
            .where(Committee.place_id==Place.id)
            .where(Committee.type_id==self.id)
            .where(CommitteeRole.committee_type_id==self.id)
            .where(CommitteeMember.committee_id==Committee.id)
            .where(CommitteeMember.role_id==CommitteeRole.id)
            .where(CommitteeMember.member_id==Member.id)
            )
        return q

    def get_all_members(self, place):
        """Returns members of all committees of this type at and below the given place.
        """
        q = self._get_members_query(place)
        return db.engine.execute(q).fetchall()


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

    def dict(self):
        return {
            "id": self.id,
            "role": self.role,
        }

    def dict(self):
        return {
            'id': self.id,
            'role': self.role,
            'multiple': self.multiple,
            'permission': self.permission
        }

    def get_permission_group(self):
        return PermissionGroup.find(self.permission)

    def __repr__(self):
        return "<Role:{}.{}>".format(self.committee_type.slug, self.role)

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

    def __repr__(self):
        return "<{}@{}>".format(self.type.slug, self.place.key)

    def get_members(self):
        """Returns an iterator over role, members for each role in this group.
        """
        d = defaultdict(list)
        for m in self.committee_members:
            # XXX-Anand: quick fix to handle the case where member is NULL for some entries.
            # possibly caused by delete volunteer
            if m.member:
                d[m.role.id].append(m.member)

        for role in self.type.roles:
            yield role, d[role.id]

    def get_members_as_list(self):
        return [m for role, members in self.get_members()
                  for m in members]

    def add_member(self, role, member):
        # TODO: Validate role and member
        # The role should be one of the roles defined in the committee type.
        # The member must be from a place in the subtree of committee's place.
        if not role or not member:
            return

        if isinstance(role, basestring):
            role = self.type.get_role(role)

        if role is None:
            raise ValueError("role can't be None.")

        # Already added
        if CommitteeMember.query.filter_by(committee=self, role=role, member=member).first():
            return
        committee_member = CommitteeMember(self, role, member)
        db.session.add(committee_member)

    def remove_member(self, role, member):
        m = CommitteeMember.query.filter_by(committee_id=self.id, role_id=role.id, member_id=member.id).first()
        if m:
            db.session.delete(m)

    def dict(self):
        return {
            "id": self.id,
            "name": self.type.name,
            "place_key": self.place.key,
            "place_name": self.place.name,
        }

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


@Place.mixin
class CommitteePlaceMixin:
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

    def get_committee(self, slug, _create=True):
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
            if not c and _create:
                c = Committee(self, committee_type)
            return c

    def get_closest_committee(self, slug):
        """Returns the commiteee with given slug attached to this place
        or any place up in the hierarchy.

        Useful for finding admin of a place etc.
        """
        c = self.get_committee(slug, _create=False)
        if c and c.committee_members:
            return c
        elif self.iparent:
            return self.iparent.get_closest_committee(slug)
