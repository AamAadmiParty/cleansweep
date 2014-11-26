from flask_wtf import Form
from wtforms import IntegerField
from wtforms import validators

class AddForm(Form):
    x = IntegerField('X', [validators.Required()])
    y = IntegerField('Y', [validators.Required()])