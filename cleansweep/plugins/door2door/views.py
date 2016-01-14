from cleansweep.plugin import Plugin
from cleansweep.view_helpers import require_permission
from flask import render_template

plugin = Plugin("door2door", __name__, template_folder="templates")


plugin.define_permission(
    name='door2door.view',
    description='Permission to view door to door entries'
)


def init_app(app):
    plugin.init_app(app)


@plugin.route("/<place:place>/door2door", methods=['GET'])
@require_permission("door2door.view")
def door2door(place):
    return render_template("door2door.html", place=place)

