"""All account related views.

Includes login, signup, oauth handlers etc.
"""
from flask import (render_template, request, redirect, url_for, flash, session)
from ..app import app
from ..models import Member
from rauth import OAuth2Service
import functools

facebook = OAuth2Service(
    client_id=app.config['FACEBOOK_CLIENT_ID'],
    client_secret=app.config['FACEBOOK_CLIENT_SECRET'],
    name='facebook',
    authorize_url='https://graph.facebook.com/oauth/authorize',
    access_token_url='https://graph.facebook.com/oauth/access_token',
    base_url='https://graph.facebook.com/')

@app.route("/account/login")
def login():
    return render_template("login.html")

@app.route("/account/logout")
def logout():
    session.pop('user')
    return redirect(url_for("home"))

@app.route("/account/login/google")
def login_google():
    return "hello google"

@app.route("/account/login/facebook")
def login_facebook():
    redirect_uri = 'http://0.0.0.0:5000/oauth/facebook'
    params = {'scope': 'email',
              'response_type': 'code',
              'redirect_uri': redirect_uri}
    url = facebook.get_authorize_url(**params)
    return redirect(url)

@app.route("/oauth/google")
def oauth_google():
    pass

def login_handler(f):
    @functools.wraps(f)
    def g():
        email = f()
        if email:
            m = Member.find(email=email)
            if m:
                session['user'] = m.email
                return redirect(url_for("dashboard"))
            else:
                flash("Sorry, could't find any user with that email.", category="error")
                return redirect(url_for("login"))
        else:
            flash("Login failed", category='error')
            return redirect(url_for("login"))
    return g

@app.route("/oauth/facebook")
@login_handler
def oauth_facebook():
    redirect_uri = 'http://0.0.0.0:5000/oauth/facebook'
    try:
        auth_session = facebook.get_auth_session(data={'code': request.args['code'],
                                              'redirect_uri': redirect_uri})
    except Exception:
        app.logger.error("Failed to authenticate facebook oauth", exc_info=True)
        return None
    user = auth_session.get('me').json()
    return user['email']

@app.route("/dashboard")
def dashboard():
    if session.get('user'):
        return render_template("dashboard.html")
    else:
        return redirect(url_for("home"))