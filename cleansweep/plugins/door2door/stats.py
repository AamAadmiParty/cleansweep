import datetime
from cleansweep.models import db
from cleansweep.stats import Stats, register_stats

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
        q = (
            "SELECT created_date as date, count(*) as count" +
            " FROM door2door_entry, place_parents p" +
            " WHERE place_id=p.child_id" +
            "   AND p.parent_id=%s" +
            "   AND created_date > %s" +
            "   AND created_date <= %s"
            " GROUP BY 1" +
            " ORDER BY 1 desc")
        result = db.engine.execute(q, [place.id, begin_date, end_date])
        return list(result)

    def get_total(self, place):
        q = (
            "SELECT count(*) as count FROM door2door_entry, place_parents p" +
            " WHERE place_id=p.child_id" +
            "   AND p.parent_id=%s"
            )
        result = db.engine.execute(q, [place.id, begin_date, end_date])
        return result.fetchone()[0]

    def get_stats(self, place):
        pass
