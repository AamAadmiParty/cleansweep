from ..plugin import Plugin
from ..models import db, Member
from flask import (render_template, abort)
from . import models, stats

plugin = Plugin("elections", __name__, template_folder="templates")

def init_app(app):
    plugin.init_app(app)

@plugin.place_view("/booths", permission='read')
def booth_report(place):
    return render_template("reports/booths.html", place=place)

@plugin.place_view("/campaigns")
def campaigns(place):
    """Dashboard for campaigns.
    """
    return render_template("campaigns/index.html", place=place)

@plugin.place_view("/campaigns/<slug>")
def view_campaign(place, slug):
    return render_template("campaigns/view.html", place=place, slug=slug)

@plugin.place_view("/campaigns/<slug>/data")
def campaign_data(place, slug):
    return render_template("campaigns/data.html", place=place, slug=slug)
