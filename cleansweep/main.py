import os
from . import utils, view_helpers
from .app import app
from .models import db
from . import notifications
from .voterlib import voterdb

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

    voterdb.init_app(app)

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