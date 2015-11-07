"""Module to initialize the app and use it using gunicorn.
"""
from .main import init_app
app = init_app(None)
