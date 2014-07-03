"""All account related views.

Includes login, signup, oauth handlers etc.
"""
from flask import render_template, request, redirect
from ..app import app
from ..models import Member
from rauth import OAuth2Service

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

@app.route("/oauth/facebook")
def oauth_facebook():
    redirect_uri = 'http://0.0.0.0:5000/oauth/facebook'
    session = facebook.get_auth_session(data={'code': request.args['code'],
                                              'redirect_uri': redirect_uri})
    user = session.get('me').json()
    m = Member.find(user['email'])
    if m:
        return "you are logged in as " + m.email
    else:
        return "sorry, no user with that email found."