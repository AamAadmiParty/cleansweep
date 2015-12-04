"""Helpers functions to use in templates.

Includes template filters and context processors.
"""
from flask import (request, session, g, url_for)
from jinja2 import Markup
import datetime
import humanize
from .app import app
from .core import rbac
from .widgets import render_widget
from .models import Member, Place, PlaceType
from . import oauth
from .voterlib import VoterDB
from . import stats
import json

sidebar_entries = []

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


@app.template_filter()
def json_encode(value):
    return Markup(json.dumps(value))


def get_current_user():
    if session.get('user'):
        return Member.find(email=session['user'])


def get_site_title():
    place = getattr(g, "place", None)
    state = place and place.get_parent('STATE')
    if state:
        key = state.code + '_SITE_TITLE'
        return app.config.get(key) or app.config.get("SITE_TITLE")
    return app.config.get("SITE_TITLE")

def changeview(endpoint=None, **view_args):
    """Returns URL for the current view, with some arguments replaced.

    For example, when the current URL is "DL/volunteers"

        changeview(key="DL/AC001")

    will return "DL/AC001/volunteers"
    """
    endpoint = endpoint or request.endpoint
    view_args = dict(request.view_args, **view_args)
    return url_for(endpoint, **view_args)

def is_phone_valid(phone):
    from .core.smslib import BaseSMSProvider
    phone = BaseSMSProvider()._process_phone(phone)
    return phone and len(phone) == 10

@app.before_request
def initiaze_default_permissions():
    """Initializes the default permissions available for the current user.

    Additional permissions based on the current location are set separately
    when executing a place_view. see view_helper.place_view for more details.
    """
    user = get_current_user()
    if user:
        g.permissions = get_permissions(user, None)
    else:
        g.permissions = []

def get_permissions(user, place):
    """Returns the list of permissions the user has at the given place.
    """
    perms = []
    # ADMIN_USERS have all the permissions
    if user.email in app.config['ADMIN_USERS']:
        perms = ['*', 'read', 'write', 'admin', 'siteadmin', 'volunteers.view']


    if place is None:
        perms += []
    else:
        place_keys = [place.key] + [p.key for p in place.parents]
        perm_dicts = rbac.get_user_permissions(user)
        perms += [p['permission'] for p in perm_dicts if p['place'] in place_keys]
    return perms

def has_permission(permission):
    """Checks if the current user has specified permission at the current place.
    """
    # g.permissions is set in view_helpers.place_view before executing the view function.
    # * indicates all permissions
    return permission in g.permissions or '*' in g.permissions

def safeint(strvalue, default=0, minvalue=None, maxvalue=None):
    """Returns the int of strvalue or default.

    Tries to convert the given string value to int.
    Returns that value if conversion is successful.
    If the given string is not a valid string the default value is returned.
    If the converted number is not within specified minvalue and maxvalue,
    the value get truncated to minvalue or maxvalue.
    """
    try:
        value = int(strvalue)
    except ValueError:
        return default

    if minvalue is not None and value < minvalue:
        return minvalue

    if maxvalue is not None and value > maxvalue:
        return maxvalue

    return value

@app.context_processor
def helpers():
    return {
        "len": len,
        "int": int,
        "list": list,
        "request_path": request.path,
        "widget": render_widget,
        "user": get_current_user(),
        "get_toplevel_places": Place.get_toplevel_places,
        "get_config": app.config.get,
        "get_oauth_providers": oauth.get_oauth_providers,
        "permissions": getattr(g, "permissions", []),
        "has_permission": has_permission,
        "voterdb": VoterDB(app.config["VOTERDB_URL"]),
        "sidebar_entries": sidebar_entries,
        "get_stats": stats.get_stats,
        "get_stat": stats.get_stat,
        "today": datetime.datetime.today(),
        "yesterday": datetime.datetime.today() - datetime.timedelta(days=1),
        "get_site_title": get_site_title,
        "changeview": changeview,
        "is_phone_valid": is_phone_valid,
        "get_user_permissions": rbac.get_user_permissions,
        "get_user_roles": rbac.get_user_roles
    }

@app.context_processor
def place_types():
    types = PlaceType.all()
    return dict((t.short_name, t) for t in types)