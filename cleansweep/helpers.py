"""Helpers functions to use in templates.

Includes template filters and context processors.
"""
from flask import (request, session, g)
import humanize
from .app import app
from .widgets import render_widget
from .models import Member, Place, MVRequest
from . import oauth

@app.template_filter('pluralize')
def pluralize(name):
    """Returns plural form of name.

        >>> pluralize('Polling Booth')
        'Polling Booths'
        >>> pluralize('Assembly Constituency')
        'Assembly Constituencies'
    """
    if name.endswith("y"):
        return name[:-1] + "ies"
    else:
        return name + 's'

@app.template_filter()
def naturaltime(datetime):
    return humanize.naturaltime(datetime)


def get_current_user():
    if session.get('user'):
        return Member.find(email=session['user'])

@app.context_processor
def helpers():
    return {
        "request_path": request.path,
        "widget": render_widget,
        "user": get_current_user(),
        "get_toplevel_places": Place.get_toplevel_places,
        "get_config": app.config.get,
        "get_oauth_providers": oauth.get_oauth_providers,
        "permissions": getattr(g, "permissions", []),
        "get_mv_request_status": MVRequest.get_request_status,
    }