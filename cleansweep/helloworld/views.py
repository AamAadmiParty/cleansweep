"""The views module defines the views, the webpages with URLs.

"""
from flask import request, render_template

# Import the Plugin class, which is a extension of Flask Blueprint.
from ..plugin import Plugin

# required for our second view
from . import forms

plugin = Plugin("helloworld", __name__, template_folder="templates")

def init_app(app):
    """Initalized the plugin, called by main.py to load this plugin.
    """
    # and intialize the plugin
    plugin.init_app(app)

# place_view is decorator that added a view for every place.
# /DL/hello /DL/AC061/hello etc.
@plugin.place_view("/hello", sidebar_entry="Hello World")
def hello(place):   
    # This function is calling the templates/hello.html template with place as argument.
    return render_template("hello.html", place=place)

# A plugin can also have more sophisticated views. 
# Lets try building something for fun.

@plugin.place_view("/add", methods=["GET", "POST"])
def add(place):
    """This is fun view to add 2 numbers.
    """
    form = forms.AddForm()
    if request.method == "POST" and form.validate():
        x = form.x.data
        y = form.y.data
        return render_template("add.html", place=place, form=form, result=x+y)
    else:
        return render_template("add.html", place=place, form=form)