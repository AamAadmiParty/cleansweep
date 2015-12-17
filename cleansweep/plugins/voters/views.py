from ...plugin import Plugin
from flask import (flash, request, render_template)
from ...voterlib import voterdb
from ...view_helpers import require_permission

plugin = Plugin("voters", __name__, template_folder="templates")

def init_app(app):
    plugin.init_app(app)
    plugin.add_sidebar_entry("Voters", endpoint="voters", permission="write")
    voterdb.init_app(app)


@plugin.route("/<place:place>/voters", methods=['GET', 'POST'])
@require_permission("write")
def voters(place):
    page = int(request.args.get('page', 1))
    return render_template("voters.html", place=place, page=page)

@plugin.route("/<place:place>/voters/<path:voterid>", methods=['GET', 'POST'])
@require_permission("write")
def voter_view(place, voterid):
    voter = voterdb.get_voter(voterid)
    if not voter:
        return abort(404)

    if request.method == 'POST':
        flash('This is still work in progress, please try again after couple of days.', category='warning')
    return render_template("voter.html", place=place, voter=voter)
