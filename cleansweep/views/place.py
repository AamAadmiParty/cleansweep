from flask import render_template, abort, session, url_for, redirect
from werkzeug.routing import BaseConverter
from ..app import app
from ..models import Place

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

app.url_map.converters['place'] = PlaceConverter

@app.route("/")
def home():
    if session.get('user'):
        return redirect(url_for("dashboard"))
    else:
        return render_template("home.html")

@app.route("/<place:key>")
def place(key):
    place = Place.find(key)
    if not place:
        abort(404)
    else:
        return render_template("place.html", place=place)

@app.route("/<place:key>/members")
def members(key):
    place = Place.find(key)
    if not place:
        abort(404)
    else:
        return render_template("members.html", place=place)
