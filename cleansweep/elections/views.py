from ..plugin import Plugin
from ..models import db, Member
from .models import Campaign, CampaignStatusTable, CampaignDataTable, BoothAgentReport
from flask import (render_template, abort, request, flash, redirect, url_for, make_response)
from . import models, stats, forms
from ...view_helpers import require_permission

import json

plugin = Plugin("elections", __name__, template_folder="templates")

def init_app(app):
    plugin.init_app(app)
    plugin.add_sidebar_entry("Booth Agents", endpoint="booth_agents", permission="write")


@plugin.route("/<place:place>/booths")
@require_permission('read')
def booth_report(place):
    return render_template("reports/booths.html", place=place)

@plugin.route("/<place:place>/campaigns")
def campaigns(place):
    """Dashboard for campaigns.
    """
    campaigns = place.get_campaigns()    
    return render_template("campaigns/index.html", place=place, campaigns=campaigns)


@plugin.route("/<place:place>/campaigns/add", methods=['GET', 'POST'])
@require_permission("write")
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
        return redirect(url_for(".campaigns", place=place))
    else:
        return render_template("campaigns/add.html", place=place, form=form)


@plugin.route("/<place:place>/campaigns/<slug>")
def view_campaign(place, slug):
    c = place.get_campaign(slug)
    status_table = CampaignStatusTable(place, c)
    return render_template("campaigns/view.html", place=place, campaign=c, status_table=status_table)

@plugin.route("/<place:place>/campaigns/<slug>/status", methods=['GET', 'POST'])
@require_permission("write")
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

@plugin.route("/<place:place>/campaigns/<slug>/data", methods=['GET', 'POST'])
@require_permission("write")
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

@plugin.route("/<place:place>/booth-agents")
@require_permission("write")
def booth_agents(place):
    if place.type.short_name not in ["AC", "STATE", "LB", "PX"]:
        return redirect(url_for("place", place=place), code=303)
    if place.type.short_name in ['AC', 'LB', 'PX']:
        report = BoothAgentReport(place)
    else:
        report = None
    return render_template("booth_agents.html", place=place, report=report)

@plugin.route("/<place:place>/booth-agents/data", methods=['GET', 'POST'])
@require_permission("write")
def booth_agents_data(place):
    if place.type.short_name not in ["AC", "LB", "PX"]:
        return redirect(url_for("place", place=place), code=303)
    report = BoothAgentReport(place)

    if request.method == 'POST':
        data = json.loads(request.form['data'])
        report.update_data(data)
        db.session.commit()
        flash("The data has been saved successfully.")

        response = make_response('{"status": "ok"}', 200)
        response.headers['Content-type'] = 'application/json'
        return response
    else:
        return render_template("booth_agents_data.html", place=place, report=report)

@plugin.route("/<place:place>/booth-agents/data-sheet", methods=['GET', 'POST'])
@require_permission("write")
def booth_agents_data_sheet(place):
    if place.type.short_name not in ["AC", "LB", "PX"]:
        return redirect(url_for("place", place=place), code=303)
    report = BoothAgentReport(place)

    if request.method == 'POST':
        data = json.loads(request.form['data'])
        report.update_data(data)
        db.session.commit()
        flash("The data has been saved successfully.")

        response = make_response('{"status": "ok"}', 200)
        response.headers['Content-type'] = 'application/json'
        return response
    else:
        return render_template("booth_agents_data_sheet.html", place=place, report=report)
