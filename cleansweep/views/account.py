"""All account related views.

Includes login, signup, oauth handlers etc.
"""
from flask import (abort, render_template, request, redirect, url_for, flash, session, jsonify)
from ..app import app
from ..models import Member, PendingMember, Place
from .. import oauth
from .. import forms
from ..core import signals
from .. import helpers as h

import random
import string
import hmac
import time
import urllib

@app.route("/account/login")
def login():
    if request.args.get('next'):
        session['login_redirect_url'] = request.args['next']
    userdata = session.get("oauth")
    app.logger.info("userdata: %s", userdata)
    if userdata:
        user = Member.find(email=userdata['email'])
        if user:
            session['user'] = user.email
            signals.login_successful.send(user, userdata=userdata)
            url = session.get("login_redirect_url") or url_for("dashboard")
            return redirect(url)
        else:
            return render_template("login.html", userdata=userdata, error=True)
    else:
        return render_template("login.html", userdata=None)

@app.route("/account/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))

def get_host(provider):
    # Microsoft doesn't allow 127.0.0.1 and Yahoo doesn't allow even localhost
    if request.host == '127.0.0.1:5000' and provider == 'microsoft':
        return 'localhost:5000'
    else:
        return request.host

def get_redirect_uri(provider):
    return 'http://{}/oauth/{}'.format(get_host(provider), provider)

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

@app.route("/account/remoteauth")
def remoteauth():
    """Simple hack to allow remote servcies to authenticate users of this system.

    This is similar to OAuth, but a lot simpler. Excepts the following query parameters:

        * client_key
        * redirect_uri
    """
    redirect_uri = request.args['redirect_uri']
    user = h.get_current_user()
    if user:
        token = user2token(user)
        return redirect(redirect_uri + "?" + urllib.urlencode(dict(token=token)))
    else:
        return redirect(url_for('login', next=url_for('remoteauth', redirect_uri=redirect_uri)))

@app.route("/account/remoteauth/userinfo", methods=['POST'])
def remoteauth_userinfo():
    token = request.form.get('token')
    user = token2user(token)
    if not user:
        return jsonify(
                status='failed',
                code='error_token_invalid',
                message='Token is either invalid or expired.')
    else:
        return jsonify(
            status='ok',
            user=dict(name=user.name, email=user.email))

@app.route("/account/remoteauth/authorize", methods=['POST'])
def remoteauth_authorizarion():
    token = request.form.get('token')
    place_key = request.form.get('place')
    #client_key = request.args['client_key']
    #client_secret = request.args['client_secret']

    user = token2user(token)
    place = Place.find(key=place_key)

    if not user:
        return jsonify(
                status='failed',
                code='error_token_invalid',
                message='Token is either invalid or expired.')
    if not place:
        return jsonify(
                status='failed',
                code='error_invalid_input',
                message='Invalid Place')

    if not user.has_permission(place, 'write'):
        return jsonify(
                status='failed',
                code='error_permission_denied',
                message="User doesn't have permission to modify data at this place.")

    return jsonify(
            status='ok',
            code='authorized',
            message='The user is authorized to modify data at this place.')



def remoteauth_error(errorcode, message):
    return jsonify(status='failed',
                   error=errorcode,
                   message=message)


def random_string(length=4):
    return "".join(random.choice(string.letters) for i in range(length))

def generate_hash(message, salt=None):
    # Assume salt is always 4 chars
    salt = salt or random_string(length=4)
    digest = hmac.HMAC(app.config['SECRET_KEY'], salt + message).hexdigest()
    return "{}-{}-{}".format(salt, digest, message)

def user2token(user):
    """Token contains 4 parts.

    userid, salt, hash, timestamp
    """
    userid = user.id
    t = int(time.time())
    message = "{:x}-{:x}".format(userid, t)
    return generate_hash(message)

def token2user(token):
    salt, digest, useridx, tx = token.split("-")
    userid = int(useridx, 16)
    t = int(tx, 16)
    message = "{:x}-{:x}".format(userid, t)

    tnow = int(time.time())

    print salt, digest, userid, t, tnow, tnow-t

    # Token is valid only for 1 hour
    if tnow - t > 3600:
        return None

    if generate_hash(message, salt) == token:
        return Member.find(id=userid)
