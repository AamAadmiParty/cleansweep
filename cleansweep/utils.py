import logging
from logging import StreamHandler
from flask_errormail import mail_on_500
from opbeat.contrib.flask import Opbeat

def setup_error_emails(app):
    """Sets up emails on errors if the SMTP server is specified in the settings.
    """
    if 'OPBEAT' in app.config:
        app.logger.info("setting up opbeat")
        config = app.config['OPBEAT']
        opbeat = Opbeat(app,
            organization_id=config['ORGANIZATION_ID'],
            app_id=config['APP_ID'],
            secret_token=config['SECRET_TOKEN'])

    if app.debug:
        return

    if 'ERROR_EMAIL_RECIPIENTS' not in app.config:
      return

    sender = app.config.get("MAIL_DEFAULT_SENDER")
    recipients = app.config['ERROR_EMAIL_RECIPIENTS'].split(",")
    mail_on_500(app, recipients, sender=sender)

def setup_logging(app):
    app.logger.setLevel(logging.INFO)
    app.logger.addHandler(StreamHandler())
