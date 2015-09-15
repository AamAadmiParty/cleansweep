import os
from flask_debugtoolbar import DebugToolbarExtension
from . import utils, view_helpers
from .app import app
from .models import db
from . import notifications
from .voterlib import voterdb
from . import plugin

def init_app(app):
    app.config.from_object('cleansweep.default_settings')

    # Hack to make it easier to specify production config
    app.config.from_pyfile('../production.cfg', silent=True)

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

    if app.debug:
        app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False
        toolbar = DebugToolbarExtension()
        toolbar.init_app(app)

    if app.debug or app.config.get("ENABLE_MOCKDOWN") == "true":
        import mockdown
        app.register_blueprint(mockdown.mockdown_app, url_prefix="/mockups")
        mockdown._mockdown.set_root("mockups")

    app.logger.info("Starting cleansweep app")

# must be done before loading view
init_app(app)

# load all helpers
from . import helpers

# load all the views
from . import views



def main(port=5000):
    db.create_all()
    app.run(port=port)

if __name__ == '__main__':
    main()
