from flask_wtf import Form
from wtforms import StringField, TextAreaField
from wtforms import validators

class NewCampaignForm(Form):
    name = StringField('Name', [validators.Required()])
    description = TextAreaField('Description', [])

