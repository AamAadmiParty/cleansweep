"""Helpers functions to use in templates.

Includes template filters and context processors.
"""
from .app import app
from .widgets import render_widget

@app.template_filter('pluralize')
def pluralize(name):
    """Returns plural form of name.

        >>> pluralize('Polling Booth')
        'Polling Booths'
        >>> pluralize('Assembly Constituency')
        'Assembly Constituencies'
    """
    if name.endswith("y"):
        return name[:-1] + "ies"
    else:
        return name + 's'

@app.context_processor
def helpers():
    return {
        "widget": render_widget
    }