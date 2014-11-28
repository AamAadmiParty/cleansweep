from ..plugin import Plugin
from ..models import db, Member
from flask import (render_template, abort)
from . import models

plugin = Plugin("elections", __name__, template_folder="templates")

def init_app(app):
    plugin.init_app(app)

@plugin.place_view("/booths", permission='read')
def booth_report(place):
    return render_template("reports/booths.html", place=place)