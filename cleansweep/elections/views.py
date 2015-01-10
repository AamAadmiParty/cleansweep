from ..plugin import Plugin
from ..models import db, Member
from .models import Campaign, CampaignStatusTable, CampaignDataTable
from flask import (render_template, abort, request, flash, redirect, url_for, make_response)
from . import models, stats, forms

import json

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
    campaigns = place.get_campaigns()    
    return render_template("campaigns/index.html", place=place, campaigns=campaigns)


@plugin.place_view("/campaigns/add", permission='write', methods=['GET', 'POST'])
def add_campaign(place):
    """Add new campaign.
    """
    if place.type.short_name != "STATE":
        abort(404)

    form = forms.NewCampaignForm(place)
    if request.method == 'POST' and form.validate():
        name = form.name.data
        slug = form.slug.data
        c = Campaign(place, slug, name)
        db.session.add(c)
        db.session.commit()
        flash("{} has been created successfully.".format(name))        
        return redirect(url_for(".campaigns", key=place.key))
    else:
        return render_template("campaigns/add.html", place=place, form=form)


@plugin.place_view("/campaigns/<slug>")
def view_campaign(place, slug):
    c = place.get_campaign(slug)
    status_table = CampaignStatusTable(place, c)
    return render_template("campaigns/view.html", place=place, campaign=c, status_table=status_table)

@plugin.place_view("/campaigns/<slug>/status", permission='write', methods=['GET', 'POST'])
def campaign_status(place, slug):
    if place.type.short_name != "AC":
        abort(404)

    c = place.get_campaign(slug)
    status_table = CampaignStatusTable(place, c)

    if request.method == 'POST':
        data = json.loads(request.form['data'])
        status_table.update(data)
        db.session.commit()
        flash("The status has been saved successfully.")

        response = make_response('{"status": "ok"}', 200)
        response.headers['Content-type'] = 'application/json'
        return response
    return render_template("campaigns/status.html", place=place, campaign=c, status_table=status_table)

@plugin.place_view("/campaigns/<slug>/data", permission='write', methods=['GET', 'POST'])
def campaign_data(place, slug):
    if place.type.short_name != "AC":
        abort(404)

    # WARNING - not tested
    c = place.get_campaign(slug)
    data_table = CampaignDataTable(place, c)

    if request.method == 'POST':
        data = json.loads(request.form['data'])
        status_table.update(data)
        db.session.commit()
        flash("The status has been saved successfully.")

        response = make_response('{"status": "ok"}', 200)
        response.headers['Content-type'] = 'application/json'
        return response
    return render_template("campaigns/data.html", place=place, campaign=c, data_table=data_table)
