from flask import Flask
import os
from .utils import setup_error_emails

app = Flask(__name__)
app.config.from_object('cleansweep.default_settings')

if os.getenv('CLEANSWEEP_SETTINGS'):
    app.config.from_envvar('CLEANSWEEP_SETTINGS')

setup_error_emails(app)