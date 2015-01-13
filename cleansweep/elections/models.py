from ..models import db, Place, PlaceType
from ..committees.models import Committee, CommitteeMember, CommitteeType
from collections import defaultdict
from sqlalchemy.sql.expression import func
from sqlalchemy.dialects.postgresql import JSON
from flask import g
import functools
import datetime

def memoize(f):
    @functools.wraps(f)
    def f2(self, *args):
        try:
            cache = g.cache
        except AttributeError:
            g.cache = cache = {}

        key = (self.key, f.__name__) + args
        if key not in cache:
            cache[key] = f(self, *args)
        return cache[key]
    return f2
 
@Place.mixin
class ElectionPlaceMixin:
    @memoize
    def _get_places_dict(self):
        places = self.get_all_child_places(type=None)
        return dict((p.id, p) for p in places)

    @memoize
    def get_place_type_id(self, short_name):
        return PlaceType.get(short_name).id

    @memoize
    def get_polling_booths(self):
        PB = self.get_place_type_id("PB")
        places = self._get_places_dict().values()
        return [p for p in places if p.type_id == PB]

    def get_booths_by_px(self):
        """Returns all booths of this place, grouped by px.

        The output will be of this format:

            [
                px1, [pb11, pb12, pb13],
                px2, [pb21],
                None, [pb_1, pb_2]
            ]
        """
        places = self.get_all_child_places(type=None)
        placesdict = dict((p.id, p) for p in places)

        PX = self.get_place_type_id("PX")

        polling_booths = self.get_polling_booths()

        d = defaultdict(list)
        for pb in polling_booths:
            px = placesdict.get(pb.iparent_id)
            if px.type_id != PX:
                px = None
            d[px].append(pb)

        print self.get_booth_agent_counts()

        #print d
        return sorted(d.items(), key=lambda item: item and item[0].code)

    def get_booth_agent_counts(self):
        booths = self.get_polling_booths()
        booth_ids = [b.id for b in booths]

        booth_committe_slug = "booth-committee"
        PB = self.get_place_type_id("PB")
        committee_type = db.session.query(CommitteeType.id).filter_by(slug=booth_committe_slug, place_type_id=PB).as_scalar()

        q = (db.session.query(Committee.place_id, func.count(CommitteeMember.id).label("count"))
            .filter(
                Committee.type_id==committee_type,
                CommitteeMember.committee_id==Committee.id,
                Committee.place_id.in_(booth_ids))
            .group_by(Committee.place_id))
        return dict((row.place_id, row.count) for row in q.all())

    def get_booth_incharges(self):
        booths = self.get_polling_booths()
        booth_ids = [b.id for b in booths]

        booth_committe_slug = "booth-committee"
        PB = self.get_place_type_id("PB")
        committee_type = db.session.query(CommitteeType.id).filter_by(slug=booth_committe_slug, place_type_id=PB).as_scalar()

        q = (db.session.query(Committee.place_id, CommitteeMember.member_id)
            .filter(
                Committee.type_id==committee_type,
                CommitteeMember.committee_id==Committee.id,
                Committee.place_id.in_(booth_ids)))

    def get_campaigns(self):
        parent_ids = [p.id for p in self._parents]
        q = Campaign.query.filter(Campaign.place_id.in_(parent_ids))
        return q.all()

    def get_campaign(self, slug):
        parent_ids = [p.id for p in self._parents]
        q = Campaign.query.filter(Campaign.place_id.in_(parent_ids), Campaign.slug == slug)
        return q.first()

class Campaign(db.Model):
    __table_args__ = (db.UniqueConstraint('place_id', 'slug'), {})

    id = db.Column(db.Integer, primary_key=True)
    slug = db.Column(db.Text, nullable=False)
    name = db.Column(db.Text, nullable=False)
    place_id = db.Column(db.Integer, db.ForeignKey("place.id"), nullable=False, index=True)

    def __init__(self, place, slug, name):
        self.place_id = place.id
        self.slug = slug
        self.name = name

class CampaignStatus(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    campaign_id = db.Column(db.Integer, db.ForeignKey("campaign.id"), nullable=False, index=True)
    campaign = db.relationship('Campaign')
    place_id = db.Column(db.Integer, db.ForeignKey("place.id"), nullable=False, index=True)
    place = db.relationship('Place')
    status = db.Column(db.Text, nullable=False)

    def __init__(self, place, campaign, status):
        self.place = place
        self.campaign =  campaign
        self.status = status

    @property
    def status_code(self):
        return self.status.lower().replace(" ", "-")

    def dict(self):
        name = self.place.name.split("-", 1)[-1].strip()
        return dict(code=self.place.code, name=name, status=self.status)

class CampaignStatusTable:
    """Class to manage all campaign status objects for an AC.
    """
    def __init__(self, place, campaign):
        self.place = place
        self.campaign = campaign
        self._status_dict = None

    def get_status(self, place):
        status_dict = self.get_status_dict()
        return status_dict.get(place.code)

    def get_status_dict(self):
        if self._status_dict is None:
            self._status_dict = self._get_status_dict()
        return self._status_dict

    def _get_status_dict(self):
        places = self.place.get_all_child_places(PlaceType.get('PB'))
        place_dict = {p.id:p for p in places}
        place_ids = place_dict.keys()
        result = CampaignStatus.query.filter(
            CampaignStatus.place_id.in_(place_ids),
            CampaignStatus.campaign_id==self.campaign.id).all()

        d = {s.place.code: s for s in result}
        for p in places:
            if p.code not in d:
                d[p.code] = CampaignStatus(p, self.campaign, "Not Started")
        return d

    def serialize(self):
        """Serializes the status objects as a list to display in a spreadsheet.
        """
        status_dict = self.get_status_dict()
        return sorted([s.dict() for s in status_dict.values()], key=lambda d: d['code'])

    def update(self, data):
        status_dict = self.get_status_dict()
        for row in data:
            code = row['code']
            status = status_dict[code]
            if status and status.status != row['status']:
                status.status = row['status']
                db.session.add(status)

class CampaignData(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    campaign_id = db.Column(db.Integer, db.ForeignKey("campaign.id"), nullable=False, index=True)
    place_id = db.Column(db.Integer, db.ForeignKey("place.id"), nullable=False, index=True)
    date = db.Column(db.Date, index=True)
    value = db.Column(db.Integer)

class CampaignDataTable:
    def __init__(self, place, campaign):
        self.place = place
        self.campaign = campaign
        self._data_dict = None

    def get_data_dict(self):
        if self._data_dict is None:
            self._data_dict = self._get_data_dict()
        return self._data_dict

    def _get_data_dict(self):
        q = CampaignData.query.filter_by(place_id=self.place.id, campaign_id=self.campaign.id)
        return {d.date:d.value for d in q.all()}

    def serialize(self):
        today = datetime.date.today()
        weekago = today - datetime.timedelta(days=7)

        d = self.get_data_dict() or {today: 0}
        mindate = min(min(d.keys()), weekago)
        print mindate
        return [{"date": date.isoformat(), "count": d.get(date, 0)} for date in self.daterange(mindate, today)]

    def daterange(self, start, end):
        while start <= end:
            yield start
            start = start + datetime.timedelta(days=1)

class BoothAgent(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ac_id = db.Column(db.Integer, db.ForeignKey("place.id"), nullable=False, index=True)
    booth_number = db.Column(db.Integer)
    name = db.Column(db.Text)
    email = db.Column(db.Text)
    phone = db.Column(db.Text)
    voterid = db.Column(db.Text)
    status = db.Column(db.Text)
    data = JSON()

    def __init__(self, ac, booth_number, name, phone, email, voterid, status=None):
        self.ac_id = ac.id
        self.booth_number = booth_number
        self.name = name
        self.phone = phone
        self.email = email
        self.voterid = voterid
        self.status = status

    def update(self, d):
        self.booth_number = d.get('booth_number')
        self.name = d.get('name')
        self.phone = d.get('phone')
        self.email = d.get('email')
        self.voterid = d.get('voterid')
        self.status = d.get('status')

    def dict(self):
        return dict(
            id=self.id,
            booth_number=self.booth_number,
            name=self.name,
            email=self.email,
            phone=self.phone,
            voterid=self.voterid,
            status=self.status)

class BoothAgentReport:
    def __init__(self, ac):
        self.ac = ac
        self.booth_count = len(self.ac.get_all_child_places(PlaceType.get("PB")))
        self.data = BoothAgent.query.filter_by(ac_id=self.ac.id).order_by('booth_number').all()

        counts_result = BoothAgent.query.filter_by(ac_id=self.ac.id).all()

        count_results = (db.session.query(BoothAgent.booth_number, func.count(BoothAgent.booth_number).label("count"))
                .filter(BoothAgent.ac_id==self.ac.id)
                .group_by(BoothAgent.booth_number)).all()
        self.counts = {row.booth_number:row.count for row in count_results}

    def get_status(self, booth_number):
        v = self.get_value(booth_number)
        print "get_status", booth_number
        if v == 0:
            return 'None'
        elif v == 1:
            return 'Progress'
        else:
            return 'Done'

    def get_value(self, booth_number):
        return self.counts.get(booth_number, 0)

    def serialize_data(self):
        return [row.dict() for row in self.data]

    def update_data(self, data):
        for row in data:
            self.update_row(row)
    def update_row(self, row):
        if self.has_value(row, 'name') and self.has_value(row, 'booth_number'):
            id = row.get('id')
            a = id and BoothAgent.query.filter_by(id=id).first()
            if a:
                a.update(row)
            else:
                a = BoothAgent(ac=self.ac,
                               booth_number=row.get('booth_number'),
                               name=row.get('name'),
                               phone=row.get('phone'),
                               email=row.get('email'),
                               voterid=row.get('voterid'),
                               status=row.get('status'))
            db.session.add(a)
        elif row.get('id'):
            id = row.get('id')
            a = id and BoothAgent.query.filter_by(id=id).first()
            if a:
                db.session.delete(a)

    def has_value(self, d, key):
        return d.get(key) and str(d[key]).strip()
