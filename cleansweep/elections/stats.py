from ..models import db
from ..stats import Stats, register_stats

@register_stats
class DoorToDoorStats(Stats):
    NAME = "elections.d2d-stats"
    TYPE = "timeseries"
    TITLE = "Houses Visited"
    MESSAGE = "#houses visited over time"
    cummulative = True

    def get_timeseries_data(self, place):
        data = place.get_stats("houses-visited")
        return [dict(date=row[0], count=row[1]) for row in data]

    def get_total(self, place):
        return 0