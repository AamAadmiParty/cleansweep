"""Simple plugin system based on flask blueprints.
"""
from flask import Blueprint
from . import view_helpers
from .app import app

class Plugin(Blueprint):
    def place_view(self, path, func=None, permission=None, sidebar_entry=None, *args, **kwargs):
        return view_helpers.place_view(path, 
            func=func,
            permission=permission,
            blueprint=self,
            sidebar_entry=sidebar_entry,
            *args,
            **kwargs)

    def init_app(self, app):
        app.register_blueprint(self)


def load_plugin(modname):
    app.logger.info("Loading plugin %s", modname)
    mod = __import__(modname, globals(), locals(), fromlist=["x"])
    mod.init_app(app)
