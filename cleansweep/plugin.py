"""Simple plugin system based on flask blueprints.
"""
from flask import Blueprint
from . import view_helpers
from .app import app
from .core import permissions

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
        self.logger = app.logger

    def define_permission(self, name, description):
        """Defines a new permission with given name and description.

        Delegates the calls to a function with same name in core.permissions module.
        Added here to avoid hassle of impoerting permissions in every plugin.
        """
        permissions.define_permission(name, description)


def load_plugin(modname):
    app.logger.info("Loading plugin %s", modname)
    mod = __import__(modname, globals(), locals(), fromlist=["x"])
    mod.init_app(app)
