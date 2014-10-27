"""Simple plugin system based on flask blueprints.
"""
from flask import Blueprint
from . import view_helpers


class Plugin(Blueprint):
    def place_view(self, path, func=None, permission=None, sidebar_entry=None, *args, **kwargs):
        return view_helpers.place_view(path, 
            func=func,
            permission=permission,
            blueprint=self,
            sidebar_entry=sidebar_entry,
            *args,
            **kwargs)
