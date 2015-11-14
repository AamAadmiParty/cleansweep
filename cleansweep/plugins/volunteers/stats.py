from ...models import db
from ...stats import Stats, register_stats

@register_stats
class VolunteerStats(Stats):
    NAME = "volunteer.stats"
    TYPE = "timeseries"
    TITLE = "Volunteers"
    MESSAGE = "#volunteers over time"
    cummulative = True

    def get_timeseries_data(self, place):
        q = (
            "SELECT created::date as date, count(*) as count" +
            " FROM member, place_parents p" +
            " WHERE place_id=p.child_id" +
            "   AND p.parent_id=%s" +
            " GROUP BY 1" +
            " ORDER BY 1 desc")
        result = db.engine.execute(q, [place.id])
        return list(result)

    def get_total(self, place):
        return place.get_member_count()