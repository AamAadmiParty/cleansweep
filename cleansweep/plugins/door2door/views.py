from cleansweep import forms
from cleansweep.models import Place, db
from cleansweep.plugin import Plugin
from cleansweep.view_helpers import require_permission
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


def init_app(app):
    plugin.init_app(app)


@plugin.route("/<place:place>/door2door", methods=['GET'])
@require_permission("door2door.view")
def door2door(place):
    return render_template("door2door.html", place=place)


@plugin.route("/<place:place>/door2door/add", methods=['GET', 'POST'])
@require_permission("door2door.add")
def make_entry(place):
    form = forms.Door2DoorForm(place, request.form)
    if request.method == "POST" and form.validate():
        p = Place.find(key=form.booth.data)
        p.add_door2door_entry(
            name=form.name.data,
            voters_in_family=form.voters_in_family.data,
            phone=form.phone.data)
        db.session.commit()
        return redirect(url_for(".door2door", place=place))
    return render_template("entry_door2door.html", place=place, form=form)
