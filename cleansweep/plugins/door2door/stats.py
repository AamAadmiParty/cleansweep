import datetime
from cleansweep.models import db, Door2DoorEntry, place_parents
from cleansweep.stats import Stats, register_stats
from flask import request

@register_stats
class Door2DoorStats(Stats):
    NAME = "door2door.stats"
    TYPE = "timeseries"
    TITLE = "Door2Door"
    MESSAGE = "#door2door entries over time"
    cummulative = True

    def get_timeseries_data(self, place):
        # Anand: Querying only for 90-day window to make the query faster.
        # For some reason, pg planner seems to be using the index only when
        # queried with date bounds. Otherwise it is doing seqscan.
        end_date = datetime.date.today()
        begin_date = end_date - datetime.timedelta(days=90)

        q = db.session.query(
                Door2DoorEntry.created_date.label("date"),
                db.func.count(Door2DoorEntry.id).label("count")
            ).filter(
                place_parents.c.parent_id==place.id,
                place_parents.c.child_id==Door2DoorEntry.place_id,
                Door2DoorEntry.created_date > begin_date,
                Door2DoorEntry.created_date <= end_date
            ).group_by(Door2DoorEntry.created_date)


        if 'campaign_id' in request.args:
            q = q.filter(Door2DoorEntry.details['campaign_id'].astext == request.args['campaign_id'])
        return [row._asdict() for row in q.all()]

    def get_total(self, place):
        print "get_total", place.id
        q = db.session.query(
                db.func.count(Door2DoorEntry.id).label("count")
            ).filter(
                place_parents.c.parent_id==place.id,
                place_parents.c.child_id==Door2DoorEntry.place_id
            )

        if 'campaign_id' in request.args:
            q = q.filter(Door2DoorEntry.details['campaign_id'].astext == request.args['campaign_id'])

        #return db.engine.execute(q).fetchone()[0]
        return q.first()[0]

    def get_stats(self, place):
        pass
