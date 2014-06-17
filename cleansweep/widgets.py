"""Library to provide support for widgets.

Widgets are like LEGO blocks, but they render some HTML snippet. Web pages
are built by putting a bunch of widgets together. What widgets to display in
a page can be configured dynamically so that new functionality can be added
without making code changes.

For example, the place page can contain the following widgets:

* PlaceNavigation - to display all places at the same level
* PlacesList - List of places below this place
* Members - Widget to display recent members
* Messages - Recent messages 

Widgets are implemented as templates in templates/widgets/ directory. By 
convention, CamelCase filenames are used for widgets and with .html extension.
For example, templates/widgets/HelloWorld.html

As of now arguments are explicity passed to the widgets, but that need to be 
fixed so that widgets can be selected dynamically from admin panel.
"""
from flask import render_template, Markup

def render_widget(name, **kwargs):
    """Renders a widget with given name.
    """
    path = "widgets/{}.html".format(name)
    return Markup(render_template(path, **kwargs))
