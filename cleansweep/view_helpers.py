import functools

from flask import (abort, render_template, session, g)
from werkzeug.routing import BaseConverter

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

@rbac.role_provider
def get_user_roles(user):
    if user.email in app.config['ADMIN_USERS']:
        yield {"place": "", "role": "admin"}
    yield {"place": user.place.key, "role": "volunteer"}

@rbac.permission_provider
def get_role_perms(role):
    if role.get('role') == 'volunteer':
        perms = ['read', 'volunteers.view']
    elif role.get('role') == 'admin':
        perms = ['read', 'write', 'admin', 'volunteers.view']
    else:
        perms = []
    return [{"place": role['place'], "permission": p} for p in perms]


def place_view(path, func=None, permission=None, blueprint=None, sidebar_entry=None, *args, **kwargs):
    """Decorator to simplify all views that work on places.

    Takes care of loading a place, permissions and 404 error if place is not found.

    The path parameter specifies the suffix after the place key.
    """
    if func is None:
        return functools.partial(place_view, path, permission=permission, blueprint=blueprint, sidebar_entry=sidebar_entry, *args, **kwargs)

    _app = blueprint or app

    # Handle the case of multiple view decorators
    if hasattr(func, "_place_view"):
        _app.route("/<place:key>" + path, *args, **kwargs)(func)
        return func

    if sidebar_entry:
        endpoint = kwargs.get('endpoint', func.__name__)
        if blueprint:
            entrypoint = blueprint.name + "." + endpoint
        else:
            entrypoint = endpoint
        h.sidebar_entries.append(dict(entrypoint=entrypoint, permission=permission, title=sidebar_entry, tab=func.__name__))

    @_app.route("/<place:key>" + path, *args, **kwargs)
    @functools.wraps(func)
    def f(key, *a, **kw):
        place = Place.find(key)
        if not place:
            abort(404)
        g.place = place
        user = h.get_current_user()
        if not user:
            return render_template("permission_denied.html")

        perms = h.get_permissions(user, place)
        # Put permissions in context globals, so that it can be added
        # to the template from helpers.py
        g.permissions = perms
        if permission and permission not in perms:
            return render_template("permission_denied.html")
        
        return func(place, *a, **kw)
    f._place_view = func
    return f

def require_permission(permission):
    def require_permission_decorator(f):
        @functools.wraps(f)
        def wrapped(*a, **kw):
            user = h.get_current_user()
            if not user:
                return render_template("permission_denied.html")

            perms = h.get_permissions(user, None)
            # Put permissions in context globals, so that it can be added
            # to the template from helpers.py
            g.permissions = perms
            if permission and permission not in perms:
                return render_template("permission_denied.html")

            return f(*a, **kw)
        return wrapped
    return require_permission_decorator

def admin_view(path, func=None, *args, **kwargs):
    return place_view(path, func=func, permission='write', *args, **kwargs)

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


