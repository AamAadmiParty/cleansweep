from ...models import db, Member, Place, place_parents
import datetime

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

@Place.mixin
class MissionVistaarPlaceMixin(object):
    def get_mv_request_status(self, user):
        """Returns Mission Vistaar request status at this place for given user.
        """
        request = MVRequest.find(place_id=self.id, member_id=user.id)
        if request:
            return request.status

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
