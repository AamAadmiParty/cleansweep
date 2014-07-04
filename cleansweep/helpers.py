"""Helpers functions to use in templates.

Includes template filters and context processors.
"""
from flask import session
from .app import app
from .widgets import render_widget
from .models import Member

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

def get_current_user():
    if session.get('user'):
        return Member.find(email=session['user'])

@app.context_processor
def helpers():
    return {
        "widget": render_widget,
        "user": get_current_user()
    }