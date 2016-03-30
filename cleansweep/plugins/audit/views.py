from . import models
from . import audit
from ...plugin import Plugin
from ...view_helpers import require_permission
from flask import (request, render_template)

# define the plugin
plugin = Plugin('audit', __name__, template_folder='templates')

def init_app(app):
	plugin.init_app(app)
	plugin.add_sidebar_entry("Audit Trial", endpoint="audit_trail", permission="audit")

@plugin.route("/<place:place>/audit", methods=['GET'])
@require_permission("audit")
def audit_trail(place):
	action = request.args.get("action")
	return render_template("audit.html", place=place, action=action)