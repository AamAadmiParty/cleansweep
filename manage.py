from flask.ext.script import Manager, Command
from flask.ext.migrate import Migrate, MigrateCommand

from cleansweep.main import app
from cleansweep.models import db

migrate = Migrate(app, db)

manager = Manager(app)


@manager.command
def init():
    "Initiates the application for first time use"

    from cleansweep.loaddata import init
    init()


@manager.command
def load():
    "Loads data from specified directory"

    from cleansweep.loaddata import main
    root_dir = raw_input("Directory (Input without quotations): ")
    main(root_dir)


class LoadFiles(Command):
    "Loads data from files"

    def run(self):
        raw_file_names = raw_input("File names (Separate using space): ")
        file_names = raw_file_names.split()
        from cleansweep.loaddata import main_loadfiles
        main_loadfiles(file_names)


class AddMember(Command):
    "Adds a member to the database"

    def run(self):
        from cleansweep.loaddata import add_member
        place = raw_input("Place (Ex: DL/AC062/PB0097): ")
        name = raw_input("Name: ")
        email = raw_input("Email: ")
        phone = raw_input("Phone (10 digit): ")
        add_member(place, name, email, phone)


class RunWorker(Command):
    "Runs a worker"

    def run(self):
        from cleansweep.core.mailer import run_worker
        run_worker()


class UpdateParents(Command):
    "Updates parents of all places below the specified key."

    def run(self):
        from cleansweep.loaddata import update_parents
        place_key = raw_input("Place (Ex: DL/AC062/PB0097): ")
        update_parents(place_key)


if __name__ == '__main__':
    manager.run({'db': MigrateCommand, 'load-files': LoadFiles(), 'add-member': AddMember(), 'run-worker': RunWorker(),
                 'update-parents': UpdateParents()})
