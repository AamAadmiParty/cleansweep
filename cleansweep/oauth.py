"""Module to handle OAuth.

Adopted from:
https://github.com/anandology/broadgauge/blob/master/broadgauge/oauth.py
License: BSD
"""
from .app import app
from rauth import OAuth2Service
from collections import namedtuple
import json

def get_oauth_service(provider, redirect_uri):
    """Returns an instance of OAuth2Service for the specified provider.
    """
    if provider == 'facebook':
        return Facebook(redirect_uri)
    elif provider == 'google':
        return Google(redirect_uri)

OAuthProvider = namedtuple("OAuthProvider", "name title")

def get_oauth_providers():
    """Returns an iterator over the available oauth service providers.

    Each entry in the iterator will be a namedtuple object containing
    name and title of the provider. For example:

        OAuthProvider(name='facebook', title='Facebook')
    """
    if 'FACEBOOK_CLIENT_ID' in app.config:
        yield OAuthProvider(name='facebook', title='Facebook')
    if 'GOOGLE_CLIENT_ID' in app.config:
        yield OAuthProvider(name='google', title='Google')

class Facebook(OAuth2Service):
    def __init__(self, redirect_uri):
        OAuth2Service.__init__(self,
            client_id=app.config['FACEBOOK_CLIENT_ID'],
            client_secret=app.config['FACEBOOK_CLIENT_SECRET'],
            name='facebook',
            authorize_url='https://graph.facebook.com/oauth/authorize',
            access_token_url='https://graph.facebook.com/oauth/access_token',
            base_url='https://graph.facebook.com/')
        self.redirect_uri = redirect_uri

    def get_authorize_url(self, **params):
        params.setdefault('response_type', 'code')
        params.setdefault('redirect_uri', self.redirect_uri)
        params.setdefault('scope', 'email')
        return OAuth2Service.get_authorize_url(self, **params)

    def get_auth_session(self, **kwargs):
        if 'data' in kwargs and isinstance(kwargs['data'], dict):
            kwargs['data'].setdefault('redirect_uri', self.redirect_uri)
            kwargs['data'].setdefault('grant_type', 'authorization_code')
        return OAuth2Service.get_auth_session(self, **kwargs)

    def get_userdata(self, code):
        """Returns the relevant userdata from github.

        This function must be called from githun oauth callback
        and the auth code must be passed as argument.
        """
        try:
            session = self.get_auth_session(
                    data={'code': code, 'redirect_uri': self.redirect_uri})
            d = session.get('me').json()
            return dict(
                name=d['name'],
                email=d['email'],
                facebook_id=d['id'],
                thumbnail='http://graph.facebook.com/{}/picture?type=square'.format(d['id']),
                service='Facebook')
        except KeyError, e:
            app.logger.error("failed to get user data from facebook. Error: %s",
                         str(e), exc_info=True)


class Google(OAuth2Service):
    def __init__(self, redirect_uri):
        OAuth2Service.__init__(self,
            client_id=app.config['GOOGLE_CLIENT_ID'],
            client_secret=app.config['GOOGLE_CLIENT_SECRET'],
            name='google',
            authorize_url='https://accounts.google.com/o/oauth2/auth',
            access_token_url='https://accounts.google.com/o/oauth2/token',
            base_url='https://www.googleapis.com/oauth2/v1/')
        self.redirect_uri = redirect_uri

    def get_authorize_url(self, **params):
        params.setdefault('response_type', 'code')
        params.setdefault('redirect_uri', self.redirect_uri)
        params.setdefault('scope', 'profile email')
        return OAuth2Service.get_authorize_url(self, **params)


    def get_auth_session(self, **kwargs):
        if 'data' in kwargs and isinstance(kwargs['data'], dict):
            kwargs['data'].setdefault('redirect_uri', self.redirect_uri)
            kwargs['data'].setdefault('grant_type', 'authorization_code')
        return OAuth2Service.get_auth_session(self, **kwargs)

    def get_userdata(self, code):
        """Returns the relevant userdata from github.

        This function must be called from githun oauth callback
        and the auth code must be passed as argument.
        """
        try:
            session = self.get_auth_session(data={'code': code},
                                            decoder=json.loads)
            d = session.get('userinfo').json()
            return dict(
                name=d['name'],
                email=d['email'],
                google_id=d['id'],
                service='Google')
        except KeyError, e:
            app.logger.error("failed to get user data from google. Error: %s",
                         str(e), exc_info=True)
