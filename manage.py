from flask.ext.script import Manager, Command
from flask.ext.migrate import Migrate, MigrateCommand

from cleansweep.main import app
from cleansweep.models import db

migrate = Migrate(app, db)


class CleansweepManager(Manager):
    """Flask Script Manager with some customizations.
    """
    def command(self, func=None, name=None):
        """Variant of @manager.command decorator provided by flask-script.

        Adds `do_something` function as `do-something` command. It is more convenient
        to type a hypen on command-line than an underscre.
        """
        command = Command(func)
        name = func.__name__.replace("_", "-")
        self.add_command(name, command)
        return func

manager = CleansweepManager(app)
manager.add_command('db', MigrateCommand)


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
def load_file(filename):
    "Loads data from the specified file."

    from cleansweep.loaddata import main_loadfiles
    main_loadfiles([filename])


@manager.command
def add_member(place, name, email, phone):
    "Adds a member to the database."

    from cleansweep.loaddata import add_member
    add_member(place, name, email, phone)


@manager.command
def run_worker():
    "Runs a worker."
    from cleansweep.core.mailer import run_worker
    run_worker()

@manager.command
def help():
    """Shows this help message.
    """
    print "USAGE: python manage.py command [arguments]"
    print ""
    print "The available commands are:"
    print ""
    width = max(len(name) for name in manager._commands)
    for name, command in sorted(manager._commands.items()):
        doc = getattr(command, 'help', None) or command.__doc__ or ""
        print "    {:{w}s}\t{}".format(name, doc.strip(), w=width)

if __name__ == '__main__':
    manager.run()
