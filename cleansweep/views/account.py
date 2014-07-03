"""All account related views.

Includes login, signup, oauth handlers etc.
"""
from flask import render_template
from ..app import app

@app.route("/account/login")
def login():
    return render_template("login.html")

@app.route("/account/login/google")
def login_google():
    return "hello google"