"""Default configuration, overwritten in production 
by specifying CLEANSWEEP_SETTINGS env variable.
"""
import os

# Should be changed on production
SECRET_KEY = "uXRlssdhCjiVyDZYiQlMFOYdmEvUoKHf"

SQLALCHEMY_DATABASE_URI = "sqlite:////tmp/cleansweep.db"
#SQLALCHEMY_DATABASE_URI = "postgresql:///cleansweep"
#SQLALCHEMY_ECHO = True

# This picks the right database on Heroku
if 'DATABASE_URL' in os.environ:
    SQLALCHEMY_DATABASE_URI = os.environ['DATABASE_URL']

if 'CLEANSWEEP_SECRET_KEY' in os.environ:
    SECRET_KEY = os.environ['CLEANSWEEP_SECRET_KEY']

DEBUG = True

# Facebook client id and secret for dev app
FACEBOOK_CLIENT_ID = '1472667626314160'
FACEBOOK_CLIENT_SECRET = 'b1d73b0247d72dee407251ecac5efa5c'
