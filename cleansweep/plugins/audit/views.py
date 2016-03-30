from . import models
from . import audit
from ...plugin import Plugin
from ... import helpers as h
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
    page = h.safeint(request.args.get("page", 1), default=1, minvalue=1)
    perpage = 100
    offset = (page-1)*perpage
    audit_records = place.get_audit_records(action=action, offset=offset, limit=perpage)
    return render_template("audit.html",
            place=place,
            audit_records=audit_records,
            action=action,
            page=page,
            perpage=perpage)