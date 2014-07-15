from flask import (render_template, abort, session, url_for,
    redirect, request, flash)
from werkzeug.routing import BaseConverter
from ..app import app
from ..models import Member, db
from .. import forms

class MemberConverter(BaseConverter):
    """Converter for member. Each member will have a URL like /member/1234"""
    def __init__(self, url_map, *items):
        super(MemberConverter, self).__init__(url_map)
        self.regex = '[A-Z0-9/]+'

app.url_map.converters['member'] = MemberConverter

@app.route("/member/<member:key>", methods=["GET", "POST"])
def member(key):
    member = Member.find_by_id(key)
    if not member:
        abort(404)
    else:
        form = forms.EditMemberForm(request.form)
        if request.method == "POST" and form.validate():
            # voterid is ignored for now
            for key in ("name", "email", "phone", "member_type"):
                setattr(member, key, getattr(form, key).data)
            db.session.commit()
            flash("Successfully updated", category="success")

        return render_template("member.html", member=member, form=form)

