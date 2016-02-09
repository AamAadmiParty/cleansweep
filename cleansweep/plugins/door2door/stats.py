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
        q = (
            "SELECT created::date as date, count(*) as count" +
            " FROM door2door_entry, place_parents p" +
            " WHERE place_id=p.child_id" +
            "   AND p.parent_id=%s" +
            " GROUP BY 1" +
            " ORDER BY 1 desc")
        result = db.engine.execute(q, [place.id])
        return list(result)

    def get_total(self, place):
        return place.get_member_count()

    def get_stats(self, place):
        pass
