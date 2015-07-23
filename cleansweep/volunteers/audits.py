from . import signals
from ..audit import record_audit

@signals.add_new_volunteer.connect
def on_add_new_volunteer(volunteer):
    record_audit(
        action="volunteer.added",
        timestamp=None,
        place=volunteer.place,
        person=volunteer,
        data=volunteer.dict())


@signals.download_volunteers_list.connect
def on_download_volunteers_list(place):

    record_audit(
        action="volunteers.downloaded",
        timestamp=None,
        person=None,
        place=place)
