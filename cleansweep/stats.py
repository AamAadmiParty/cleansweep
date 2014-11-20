import time
import datetime
from . import widgets

STATS = []

class Stats(object):
    cummulative = False

    @property
    def id(self):
        return self.NAME.replace(".", "-")

    @property
    def title(self):
        return self.TITLE

    @property
    def type(self):
        return self.TYPE

    def is_enabled_for(self, place):
        return True

    def get_stats(self, place):
        raise NotImplementedError()

    def get_timeseries_data(self, place):
        raise NotImplementedError()

    def get_total(self, place):
        raise NotImplementedError()

    def render(self, place):
        return widgets.render_widget("Stats", place=place, stats=self)

    def get_timeseries_data_for_graph(self, place):
        return self.prepare_data_for_graph(self.get_timeseries_data(place))

    def prepare_data_for_graph(self, rows):
        """Expects each row to have date and count fields.
        """
        rows = sorted(rows)

        today = datetime.date.today()
        yday = today - datetime.timedelta(days=1)

        rows = rows or [web.storage(date=today, count=0)]

        mindate = min(rows[0].date, yday)
        maxdate = max(rows[-1].date, today)

        d = dict((row.date, row.count) for row in rows)
        x = []
        count = 0
        for date in self.daterange(mindate, maxdate):
            v = d.get(date, 0)
            if self.cummulative:
                count += v
                value = count
            else:
                value = v
            x.append([time.mktime(date.timetuple()) * 1000, value])
        return x        

    def daterange(self, start, end):
        date = start
        while date <= end:
            yield date
            date += datetime.timedelta(days=1)        

def register_stats(cls=None):
    STATS.append(cls)
    return cls

def get_stats(place):
    return [s() for s in STATS if s().is_enabled_for(place)]

