"""Default configuration, overwritten in production 
by specifying CLEANSWEEP_SETTINGS env variable.
"""

SECRET_KEY = "uXRlssdhCjiVyDZYiQlMFOYdmEvUoKHf"
SQLALCHEMY_DATABASE_URI = "sqlite:////tmp/cleansweep.db"
SQLALCHEMY_ECHO = True