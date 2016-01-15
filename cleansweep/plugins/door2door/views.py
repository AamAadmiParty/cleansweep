from cleansweep import forms
from cleansweep.models import db, Door2DoorEntry, PlaceType
from cleansweep.plugin import Plugin
from cleansweep.view_helpers import require_permission
import cleansweep.helpers as h
from flask import render_template, request, redirect, url_for

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

def init_app(app):
    plugin.init_app(app)


@plugin.route("/door2door", methods=['GET'])
def door2door_redirect():
    user = h.get_current_user()
    if not user:
        return redirect(url_for("dashboard"))
    place = user.place.get_parent("AC")
    if not place:
        return redirect(url_for("dashboard"))
    return redirect(url_for(".door2door", place=place))

@plugin.route("/<place:place>/door2door", methods=['GET'])
@require_permission("door2door.view")
def door2door(place):
    return render_template("door2door.html", place=place)


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
            town=form.town.data)
        db.session.commit()
        return redirect(url_for(".door2door", place=place))
    return render_template("entry_door2door.html", place=place, form=form)


@plugin.route("/<place:place>/door2door/delete/<_id>")
@require_permission("door2door.delete")
def delete_entry(place, _id):
    entry = Door2DoorEntry.find(id=_id)
    db.session.delete(entry)
    db.session.commit()
    return render_template("door2door.html", place=place)

