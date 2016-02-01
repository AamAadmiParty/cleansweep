from .import signals
from cleansweep.core import smslib
from cleansweep.models import Place
from cleansweep.views.admin import get_sms_config
from flask import render_template

@signals.door2door_import.connect
def on_import(entries):
    phone_numbers = [e.phone for e in entries]

    print Place.get_toplevel_place()
    config = get_sms_config(Place.get_toplevel_place())
    print config
    sms_provider = config and smslib.get_sms_provider(**config)

    message = "Thank you for joining as member of AAP."
    sms_provider.send_sms(phone_numbers, message)
