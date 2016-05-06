import functools

from flask import (abort, request, render_template, session, g)
from werkzeug.routing import BaseConverter, ValidationError

from .core import rbac
from .models import Place, Member
import helpers as h

app = None

def init_app(_app):
    """Registeres the <place:xxx> converter with the app.

    Also remembers the app in a global var so that it can be used in other
    functions.
    """
    global app
    app = _app
    app.url_map.converters['place'] = PlaceConverter

    app.before_request(register_place_hook)

def register_place_hook():
    """Hook to take the place from the view arguments and set it in context globals.

    The place set in context globals is used by some legacy code.
    """
    if request.view_args and 'place' in request.view_args:
        g.place = request.view_args['place']

        # initialize the permissions
        user = h.get_current_user()
        if user:
            g.permissions = h.get_permissions(user, g.place)

@rbac.role_provider
def get_user_roles(user):
    if not user:
        return
    if user.email in app.config['ADMIN_USERS']:
        yield {"place": "", "role": "admin"}
    yield {"place": user.place.key, "role": "volunteer"}

@rbac.permission_provider
def get_role_perms(role):
    if role.get('role') == 'volunteer':
        perms = ['read', 'volunteers.view']
    elif role.get('role') == 'admin':
        perms = ['*', 'read', 'write', 'admin', 'volunteers.view']
    else:
        perms = []
    return [{"place": role['place'], "permission": p} for p in perms]


def require_permission(permission):
    def require_permission_decorator(f):
        @functools.wraps(f)
        def wrapped(*a, **kw):
            user = h.get_current_user()
            if not user:
                return render_template("permission_denied.html")

            # Find the current place from the view args
            # or use the top-level place
            place = request.view_args.get("place") or Place.get_toplevel_place()

            perms = h.get_permissions(user, place)
            # Put permissions in context globals, so that it can be added
            # to the template from helpers.py
            g.permissions = perms
            if permission and not h.has_permission(permission):
                return render_template("permission_denied.html")

            return f(*a, **kw)
        return wrapped
    return require_permission_decorator


class PlaceConverter(BaseConverter):
    """Converter for place.

    Places will have URLs like KA, KA/LC12, KA/AC123, KA/AC123/PB0123 etc.
    We'll also have URLS for actions on places as KA/LC12/members etc. This
    converter provide support for place converter, so that we can use routes
    like:

        @app.route(/<place:key>)
        ...

        @app.route(/<place:key>/members)
        ...
    """
    def __init__(self, url_map, *items):
        super(PlaceConverter, self).__init__(url_map)
        self.regex = '[A-Z0-9/]+'

    def to_python(self, value):
        place = Place.find(key=value)
        if not place:
            raise ValidationError()
        return place

    def to_url(self, value):
        if isinstance(value, Place):
            return value.key
        else:
            return value

class PlaceConverter(BaseConverter):
    """Converter for place.

    Places will have URLs like KA, KA/LC12, KA/AC123, KA/AC123/PB0123 etc.
    We'll also have URLS for actions on places as KA/LC12/members etc. This
    converter provide support for place converter, so that we can use routes
    like:

        @app.route(/<place:key>)
        ...

        @app.route(/<place:key>/members)
        ...
    """
    def __init__(self, url_map, *items):
        super(PlaceConverter, self).__init__(url_map)
        self.regex = '[A-Z0-9/]+'

    def to_python(self, value):
        place = Place.find(key=value)
        if not place:
            raise ValidationError()
        return place

    def to_url(self, value):
        if isinstance(value, Place):
            return value.key
        else:
            return value            