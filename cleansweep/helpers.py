"""Helpers functions to use in templates.

Includes template filters and context processors.
"""
from .app import app
from .widgets import render_widget

@app.context_processor
def helpers():
    return {
        "widget": render_widget
    }