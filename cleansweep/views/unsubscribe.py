from flask import (render_template, url_for, redirect, request, flash, jsonify)
from ..app import app
from ..models import Unsubscribe
from ..forms import UnsubscribeForm

@app.route("/unsubscribe", methods=["GET", "POST"])
def unsubscribe():
	form = UnsubscribeForm(request.form or request.args)
	if request.method == "POST" and form.validate():
		Unsubscribe.unsubscribe(form.email.data)
		return render_template("unsubscribe.html", form=form, success=True)
	else:
		return render_template("unsubscribe.html", form=form)
