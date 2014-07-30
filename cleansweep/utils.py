import logging
from logging.handlers import SMTPHandler

def setup_error_emails(app):
    """Sets up emails on errors if the SMTP server is specified in the settings.
    """
    if app.debug:
        return

    if 'MAIL_SERVER' not in app.config or 'ERROR_EMAIL_RECIPIENTS' not in app.config:
        return

    recipients = app.config['ERROR_EMAIL_RECIPIENTS'].split(",")

    MAIL_SERVER = app.config['MAIL_SERVER']
    MAIL_USERNAME = app.config['MAIL_USERNAME']
    MAIL_PASSWORD = app.config['MAIL_PASSWORD']
    from_address = app.config['MAIL_DEFAULT_SENDER']

    mail_handler = SMTPHandler(MAIL_SERVER,
                               from_address,
                               recipients,
                               'Cleansweep Failed',
                               credentials=(MAIL_USERNAME, MAIL_PASSWORD),
                               secure=True)
    mail_handler.setLevel(logging.ERROR)
    app.logger.addHandler(mail_handler)
