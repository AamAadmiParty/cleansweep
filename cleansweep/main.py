import os
from flask_debugtoolbar import DebugToolbarExtension
from . import utils, view_helpers
from .app import app
from .models import db
from . import notifications
from .voterlib import voterdb
from . import plugin
import logging

logger = logging.getLogger(__name__)

def init_app(config_file, create_tables=None):
    app.config.from_object('cleansweep.default_settings')

    if config_file:
        # take the absolute path, otherwise Flask looks for file relative to the app
        # insted of PWD.
        config_path = config_file and os.path.abspath(config_file)

        app.config.from_pyfile(config_path, silent=True)
        logger.info("init_app %s", config_path)

    if os.getenv('CLEANSWEEP_SETTINGS'):
        app.config.from_envvar('CLEANSWEEP_SETTINGS')

    utils.setup_error_emails(app)
    utils.setup_logging(app)

    # Setup the view helpers
    view_helpers.init_app(app)

    # load plugins
    plugins = app.config['DEFAULT_PLUGINS'] + app.config['PLUGINS']
    for name in plugins:
        plugin.load_plugin(name)

    # enable create_tables if a value is not speficied and the app is running in debug mode
    if create_tables is None and app.config['DEBUG']:
        create_tables = True

    if create_tables:
        db.create_all()

    if app.debug:
        app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False
        toolbar = DebugToolbarExtension()
        toolbar.init_app(app)

    if app.debug or app.config.get("ENABLE_MOCKDOWN") == "true":
        enable_mockdown()

    # load all helpers
    from . import helpers

    # load all the views
    from . import views

    app.logger.info("Starting cleansweep app")
    return app

def enable_mockdown():
    try:
        import mockdown
    except ImportError:
        logger.warn("Unable to import mockdown, skipping it...")
        return
    app.register_blueprint(mockdown.mockdown_app, url_prefix="/mockups")
    mockdown._mockdown.set_root("mockups")

def main(port=5000):
    init_app("config/development.py", create_tables=True)
    app.run(port=port)

def initdb():
    app.config.from_object('cleansweep.default_settings')
    if os.getenv('CLEANSWEEP_SETTINGS'):
        app.config.from_envvar('CLEANSWEEP_SETTINGS')
    logger.info("initializing the database...")
    db.create_all()

if __name__ == '__main__':
    main()
