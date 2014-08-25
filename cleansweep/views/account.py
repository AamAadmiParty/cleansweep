"""All account related views.

Includes login, signup, oauth handlers etc.
"""
from flask import (abort, render_template, request, redirect, url_for, flash, session)
from ..app import app
from ..models import Member, PendingMember
from .. import oauth
from .. import forms
from ..core import signups

@app.route("/account/login")
def login():
    userdata = session.get("oauth")
    app.logger.info("userdata: %s", userdata)
    if userdata:
        user = Member.find(email=userdata['email'])
        if user:
            session['user'] = user.email
            return redirect(url_for("dashboard"))
        else:
            return render_template("login.html", userdata=userdata, error=True)
    else:
        return render_template("login.html", userdata=None)

@app.route("/account/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))

@app.route("/account/signup", methods=["GET", "POST"])
def signup():
    userdata = session.get("oauth")

    # is user autheticated?
    if not userdata:
        return render_template("signup.html", userdata=None)

    # is already a member?
    user = Member.find(email=userdata['email'])
    if user:
        session['user'] = user.email
        return redirect(url_for("dashboard"))

    # is already a member?
    pending_member = PendingMember.find(email=userdata['email'])
    if pending_member:
        return render_template("signup.html", userdata=None, pending_member=pending_member)

    # show the form
    form = forms.SignupForm()
    if request.method == "GET":
        form.name.data = userdata['name']
    if request.method == "POST" and form.validate():
        person = signups.signup(
            name=form.name.data,
            email=userdata['email'],
            phone=form.phone.data,
            voterid=form.voterid.data,
            place_key=form.place.data)
        return render_template("signup_complete.html", person=person)
    return render_template("signup.html", userdata=userdata, form=form)


def get_host():
    # facebook doesn't seem to like 127.0.0.1
    if request.host == '127.0.0.1:5000' and False:
        return '0.0.0.0:5000'
    else:
        return request.host

def get_redirect_uri(provider):
    return 'http://{}/oauth/{}'.format(get_host(), provider)

@app.route("/oauth/redirect-<provider>/<view>")
def oauth_redirect(provider, view):
    """OAuth redirect hander.

    When used from login view with google as oauth provider, the URL will be
    "/oauth/redirect-google/login" or
    url_for("oauth_redirect", provider="google", view="login")
    """
    redirect_uri = get_redirect_uri(provider)
    client = oauth.get_oauth_service(provider, redirect_uri)
    if not client:
        abort(404)
    url = client.get_authorize_url()
    session['next'] = url_for(view)
    return redirect(url)

@app.route("/oauth/reset")
def oauth_reset():
    session.pop("oauth", None)
    next = request.args.get('next') or \
           request.referrer or \
           url_for('home')
    return redirect(next)

@app.route("/oauth/<provider>")
def oauth_callback(provider):
    redirect_uri = get_redirect_uri(provider)
    client = oauth.get_oauth_service(provider, redirect_uri)
    if not client:
        abort(404)

    if "code" in request.args:
        userdata = client.get_userdata(request.args['code'])
        if userdata:
            session["oauth"] = userdata
            return redirect(session.get("next"))
    flash("Authorization failed, please try again.", category="error")
    return redirect(session.get("next", url_for("home")))

@app.route("/dashboard")
def dashboard():
    if session.get('user'):
        return render_template("dashboard.html")
    else:
        return redirect(url_for("home"))