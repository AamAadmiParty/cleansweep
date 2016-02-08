"""Default configuration, overwritten in production
by specifying CLEANSWEEP_SETTINGS env variable.
"""
import os

SITE_TITLE = "Cleansweep"

# Should be changed on production
SECRET_KEY = "uXRlssdhCjiVyDZYiQlMFOYdmEvUoKHf"

SQLALCHEMY_DATABASE_URI = "postgresql:///cleansweep"
TEST_DATABASE_URI = "postgresql:///cleansweep_test"
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

MICROSOFT_CLIENT_ID = '0000000048166B2A'
MICROSOFT_CLIENT_SECRET = '52F1ZWq5upyUS9smpmQeb4LoLNa8zvnC'

TRUSTED_APPS = [
    {
        'app-name': 'cleansweep-sms-bridge',
        'client-id': 'xSbAMFEJlFrZUFyV',
        'client-secret': 'VEmleukjCvpNoVnmeIIGFaCuIJckjTBR',
        'scope': ['send-sms'],
        'ips': ['']

    }
]

ENABLE_MOCKDOWN = False

LOGGER_NAME = "cleansweep"

# Specify the list of admin users here.
ADMIN_USERS = []

# These plugins are loaded by default
DEFAULT_PLUGINS = [
    "cleansweep.plugins.volunteers",
    "cleansweep.plugins.voters",
    "cleansweep.plugins.signups",
    "cleansweep.plugins.committees",
    "cleansweep.plugins.vistaar",
    "cleansweep.plugins.audit",
]

# Specify any additional plugins that you may want to load here.
PLUGINS = []

def _load_from_config():
    g = globals()

    keys = [
        'MAIL_SERVER',
        'MAIL_USERNAME',
        'MAIL_PASSWORD',
        'MAIL_DEFAULT_SENDER',
        'ERROR_EMAIL_RECIPIENTS',
        'SQLALCHEMY_ECHO',
        'ADMIN_USERS',
        'TEST_DATABASE_URI',
        'ENABLE_MOCKDOWN',
        'DEBUG'
    ]
    for k in keys:
        if k in os.environ:
            g[k] = os.environ[k]

    # Allow specifying custom plugins from enviroment (for Heroku)
    if 'PLUGINS' in os.environ:
        g['PLUGINS'] = os.environ['PLUGINS'].split()

    # Allow ADMIN_USERS setting to be specified in the env as string
    if isinstance(g['ADMIN_USERS'], str):
        g['ADMIN_USERS'] = g['ADMIN_USERS'].split(",")

_load_from_config()

if os.getenv("CLEANSWEEP_TEST"):
    SQLALCHEMY_DATABASE_URI = TEST_DATABASE_URI
