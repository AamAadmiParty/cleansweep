from flask.ext.script import Manager
from flask.ext.migrate import Migrate, MigrateCommand

from cleansweep.main import app
from cleansweep.models import db

migrate = Migrate(app, db)

manager = Manager(app)


@manager.command
def init():
    "Initiates the application for first time use."

    from cleansweep.loaddata import init
    init()


@manager.command
def load(directory):
    "Loads data from the specified directory."

    from cleansweep.loaddata import main
    main(directory)


@manager.command
def loadfile(filename):
    "Loads data from the specified file."

    from cleansweep.loaddata import main_loadfiles
    main_loadfiles(filename)


@manager.command
def add_member(place, name, email, phone):
    "Adds a member to the database."

    from cleansweep.loaddata import add_member
    add_member(place, name, email, phone)


@manager.command
def runworker():
    "Runs a worker."

    from cleansweep.core.mailer import run_worker
    run_worker()


@manager.command
def update_parents(place):
    "Updates parents of all places below the specified key."

    from cleansweep.loaddata import update_parents
    update_parents(place)


if __name__ == '__main__':
    manager.run({'db': MigrateCommand})
