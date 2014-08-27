import functools

from flask import (abort, render_template, session)
from werkzeug.routing import BaseConverter

from .models import Place, Member

app = None

def init_app(_app):
    """Registeres the <place:xxx> converter with the app.

    Also remembers the app in a global var so that it can be used in other 
    functions.
    """
    global app
    app = _app
    app.url_map.converters['place'] = PlaceConverter

def _get_current_user():
    if session.get('user'):
        return Member.find(email=session['user'])


def place_view(path, func=None, *args, **kwargs):
    """Decorator to simplify all views that work on places.

    Takes care of loading a place, permissions and 404 error if place is not found.

    The path parameter specifies the suffix after the place key.
    """
    if func is None:
        return functools.partial(place_view, path)

    @app.route("/<place:key>" + path, *args, **kwargs)
    @functools.wraps(func)
    def f(key, *a, **kw):
        place = Place.find(key)
        if not place:
            abort(404)
        user = _get_current_user()
        if not user:
            return render_template("permission_denied.html")
        
        return func(place, *a, **kw)
    return f


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


