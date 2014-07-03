"""Default configuration, overwritten in production 
by specifying CLEANSWEEP_SETTINGS env variable.
"""

SECRET_KEY = "uXRlssdhCjiVyDZYiQlMFOYdmEvUoKHf"
SQLALCHEMY_DATABASE_URI = "sqlite:////tmp/cleansweep.db"
#SQLALCHEMY_DATABASE_URI = "postgresql:///cleansweep"
SQLALCHEMY_ECHO = True

DEBUG = True

# Facebook client id and secret for dev app
FACEBOOK_CLIENT_ID = '749942458362317'
FACEBOOK_CLIENT_SECRET = '6f67d7e52b3bbb1b52fc6c083d839aff'
