from cleansweep import forms
from cleansweep.models import db, Place, Door2DoorEntry, PlaceType
from cleansweep.plugin import Plugin
from cleansweep.view_helpers import require_permission
import cleansweep.helpers as h
from flask import render_template, request, redirect, url_for, jsonify, abort, flash
from . import signals, notifications, stats
from flask.ext.paginate import Pagination

plugin = Plugin("door2door", __name__, template_folder="templates")


plugin.define_permission(
    name='door2door.view',
    description='Permission to view door to door entries'
)

plugin.define_permission(
    name='door2door.add',
    description='Permission to make door to door entries'
)

plugin.define_permission(
    name='door2door.delete',
    description='Permission to delete door to door entries'
)

DOOR2DOOR_SECRET = None

def init_app(app):
    plugin.init_app(app)

    global DOOR2DOOR_SECRET
    DOOR2DOOR_SECRET = app.config.get('DOOR2DOOR_SECRET')


@plugin.route("/door2door", methods=['GET'])
def door2door_redirect():
    user = h.get_current_user()
    if not user or not user.place:
        return redirect(url_for("dashboard"))

    place = user.place if user.place.type >= PlaceType.get("AC") else user.place.get_parent("AC")
    endpoint = ".door2door" if request.path == "/door2door" else ".make_entry"
    return redirect(url_for(endpoint, place=place))


@plugin.route("/door2door/add", methods=['GET'])
def door2door_entry_redirect():
    return door2door_redirect()

@plugin.route("/<place:place>/door2door", methods=['GET'])
@require_permission("door2door.view")
def door2door(place):
    page = h.safeint(request.args.get('page', 1), default=1, minvalue=1)
    total = place.get_door2door_count()
    limit = 50
    pagination = Pagination(total=total, page=page, per_page=limit, bs_version=3, prev_label="&laquo; Prev",
                            next_label="Next &raquo;")
    entries = place.get_door2door_entries(limit=limit, offset=(page - 1) * limit)
    return render_template("door2door.html", place=place, entries=entries, pagination=pagination)


@plugin.route("/<place:place>/door2door/add", methods=['GET', 'POST'])
@require_permission("door2door.add")
def make_entry(place):
    # If place is greater than AC set form to None
    form = forms.Door2DoorForm(place, request.form) if place.type <= PlaceType.get("AC") else None
    if request.method == "POST" and form.validate():
        place.add_door2door_entry(
            name=form.name.data,
            voters_in_family=form.voters_in_family.data,
            phone=form.phone.data,
            town=form.town.data,
        )
        db.session.commit()
        return redirect(url_for(".door2door", place=place))
    return render_template("entry_door2door.html", place=place, form=form)


@plugin.route("/<place:place>/door2door/delete/<id>-<hash>")
@require_permission("door2door.delete")
def delete_entry(place, id, hash):
    entry = Door2DoorEntry.find(id=id)
    if not entry and entry.get_hash() != hash:
        abort(404)
    db.session.delete(entry)
    db.session.commit()
    signals.door2door_delete.send(entry, place=place)
    flash(u"Deleted entry of {}.".format(entry.name))
    return redirect(url_for(".door2door", place=place))


@plugin.route("/<place:place>/door2door/entry/<id>-<hash>")
def details(place, id, hash):
    entry = Door2DoorEntry.find(id=id)
    if not entry and entry.get_hash() != hash:
        abort(404)
    return render_template("details.html", place=place, entry=entry)



@plugin.route("/<place:place>/door2door/import", methods=["POST"])
def bulk_import(place):
    """View to bulk import door2door data.

    Protected by a secret password, shared between the API user and the server.

    The data must be sent as JSON payload. Sample payload:

        {
            "secret": "abcd1234",
            "data": [
                {
                    "ac": "AC123",
                    "town": "name of village or town",
                    "name": "Person One",
                    "phone": "1234567890",
                    "voters_in_family": 5,
                    "donation": 10
                },
                {
                    "ac": "AC123",
                    "town": "name of village or town",
                    "name": "Person Two",
                    "phone": "1234567892",
                    "voters_in_family": 2,
                    "donation": 10
                }
            ]
        }
    """
    data = request.get_json(force=True)
    if not DOOR2DOOR_SECRET or data.get("secret") != DOOR2DOOR_SECRET:
        return jsonify({
            "status": "failed",
            "error": "unauthorized",
            "message": "Please check the secret"
        }), 401

    ac_cache = {}

    def get_ac(ac_code):
        if ac_code not in ac_cache:
            key = place.key + "/" + ac_code
            p = Place.find(key)
            ac_cache[ac_code] = p
        else:
            p = ac_cache[ac_code]
        return p

    entries = []

    for row in data['data']:
        ac_code = row.pop('ac')
        ac = get_ac(ac_code)
        print("adding", row)
        entry = ac.add_door2door_entry(**row)
        entries.append(entry)
    db.session.commit()
    signals.door2door_import.send(entries)

    return jsonify(status="ok", message="successfully imported.")
