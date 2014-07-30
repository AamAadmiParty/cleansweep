from flask import Flask
import os
from . import utils

app = Flask(__name__)
app.config.from_object('cleansweep.default_settings')

if os.getenv('CLEANSWEEP_SETTINGS'):
    app.config.from_envvar('CLEANSWEEP_SETTINGS')

utils.setup_error_emails(app)
utils.setup_logging(app)

app.logger.info("Starting cleansweep app")

