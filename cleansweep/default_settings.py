"""Default configuration, overwritten in production 
by specifying CLEANSWEEP_SETTINGS env variable.
"""
import os

SITE_TITLE = "Cleansweep"

# Should be changed on production
SECRET_KEY = "uXRlssdhCjiVyDZYiQlMFOYdmEvUoKHf"

SQLALCHEMY_DATABASE_URI = "postgresql:///cleansweep"
SQLALCHEMY_ECHO = False

# This picks the right database on Heroku
if 'DATABASE_URL' in os.environ:
    SQLALCHEMY_DATABASE_URI = os.environ['DATABASE_URL']

if 'CLEANSWEEP_SECRET_KEY' in os.environ:
    SECRET_KEY = os.environ['CLEANSWEEP_SECRET_KEY']

VOTERDB_URL = None

DEBUG = True

# Facebook client id and secret for dev app
FACEBOOK_CLIENT_ID = '1472667626314160'
FACEBOOK_CLIENT_SECRET = 'b1d73b0247d72dee407251ecac5efa5c'

GOOGLE_CLIENT_ID = "563938957424-8sb0jqrkt9s8cp5hvs8lnsg66i3cq0ko.apps.googleusercontent.com"
GOOGLE_CLIENT_SECRET = "Qa-afy19Z9J6gqyqnpcHJjvQ"

# Specify the list of admin users here.
ADMIN_USERS = []

PLUGINS = [
    "cleansweep.volunteers",
    "cleansweep.voters",
    "cleansweep.signups",
    "cleansweep.committees",
    "cleansweep.vistaar",
    "cleansweep.audit",
]
DEFAULT_PLUGINS = PLUGINS

def _load_from_config():
    g = globals()

    keys = [
        'MAIL_SERVER',
        'MAIL_USERNAME',
        'MAIL_PASSWORD',
        'MAIL_DEFAULT_SENDER',
        'ERROR_EMAIL_RECIPIENTS',
        'SQLALCHEMY_ECHO'
    ]
    for k in keys:
        if k in os.environ:
            g[k] = os.environ[k]

_load_from_config()
