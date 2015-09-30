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

def init_app(config_file, create_tables=False):
    # take the absolute path, otherwise Flask looks for file relative to the app
    # insted of PWD.
    config_path = os.path.abspath(config_file)

    app.config.from_object('cleansweep.default_settings')

    # Hack to make it easier to specify production config
    app.config.from_pyfile(config_path, silent=True)

    if os.getenv('CLEANSWEEP_SETTINGS'):
        app.config.from_envvar('CLEANSWEEP_SETTINGS')

    utils.setup_error_emails(app)
    utils.setup_logging(app)
    logger.info("init_app %s", config_path)

    # Setup the view helpers
    view_helpers.init_app(app)

    # load plugins
    plugins = app.config['DEFAULT_PLUGINS'] + app.config['PLUGINS']
    for name in plugins:
        plugin.load_plugin(name)

    if create_tables:
        db.create_all()

    if app.debug:
        app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False
        toolbar = DebugToolbarExtension()
        toolbar.init_app(app)

    if app.debug or app.config.get("ENABLE_MOCKDOWN") == "true":
        import mockdown
        app.register_blueprint(mockdown.mockdown_app, url_prefix="/mockups")
        mockdown._mockdown.set_root("mockups")

    # load all helpers
    from . import helpers

    # load all the views
    from . import views

    app.logger.info("Starting cleansweep app")
    return app


def main(port=5000):
    init_app("config/development.py", create_tables=True)
    app.run(port=port)

if __name__ == '__main__':
    main()
