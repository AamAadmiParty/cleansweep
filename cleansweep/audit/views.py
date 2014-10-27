from . import models
from . import audit
from ..plugin import Plugin
from flask import (request, render_template)

# define the plugin
plugin = Plugin('audit', __name__, template_folder='templates')

def init_app(app):
	plugin.init_app(app)


@plugin.place_view("/audit", methods=['GET'], permission='admin', sidebar_entry='Audit Trail')
def audit_trail(place):
	return render_template("audit.html", place=place)