from flask_wtf import Form
from wtforms import StringField, TextAreaField
from wtforms import validators
from .models import Campaign

class NewCampaignForm(Form):
    name = StringField('Name', [validators.Required()])
    slug = StringField('Slug', [validators.Required()])
    description = TextAreaField('Description', [])

    def __init__(self, place):
        Form.__init__(self)
        self.place = place

    def validate_slug(self, field):
        slug = field.data
        if self.place.get_campaign(slug):
            raise validators.ValidationError('There is already a campaign with this slug.')
