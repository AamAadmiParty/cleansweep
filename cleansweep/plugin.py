"""Simple plugin system based on flask blueprints.
"""
from flask import Blueprint, g, render_template
import functools
from . import helpers as h

class Plugin(Blueprint):
    def init_app(self, app):
        app.register_blueprint(self)
        self.logger = app.logger

    def define_permission(self, name, description):
        """Defines a new permission with given name and description.

        Delegates the calls to a function with same name in core.permissions module.
        Added here to avoid hassle of impoerting permissions in every plugin.
        """
        from .core import permissions
        permissions.define_permission(name, description)

    def add_sidebar_entry(self, title, endpoint, permission):
        _endpoint = "{}.{}".format(self.name, endpoint)
        h.sidebar_entries.append(dict(
            entrypoint=_endpoint,
            permission=permission,
            title=title,
            tab=endpoint))

def load_plugin(modname):
    from .app import app
    app.logger.info("Loading plugin %s", modname)
    mod = __import__(modname, globals(), locals(), fromlist=["x"])
    mod.init_app(app)
