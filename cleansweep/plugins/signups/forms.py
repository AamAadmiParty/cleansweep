from flask_wtf import Form
from wtforms import StringField, HiddenField
from wtforms import validators

from ... import models

from cleansweep.core.voter_lookup import get_voter


class SignupForm(Form):
    name = StringField('Name', [validators.Required()])
    phone = StringField('Phone Number', [validators.Required()])
    voterid = StringField('Voter ID')
    locality = StringField('Locality')
    place = HiddenField()

    def validate_phone(self, field):
        phone = field.data
        if models.PendingMember.find(phone=phone) or models.Member.find(phone=phone):
            raise validators.ValidationError('This phone number is already used')

    def validate_voterid(self, field):
        # if not field.data and self.place.data == "None":  # TODO highlight locality field too
        #     raise validators.ValidationError("You must provide either a valid voter ID or locality.")

        if not field.data:
            raise validators.ValidationError("You must provide a valid voter ID.")

        if self.voterid.data:
            voterid = self.voterid.data
            voter = get_voter(voterid)
            if not voter:
                raise validators.ValidationError("Invalid Voter ID")

            place_key = voter['key']
            place = models.Place.find(place_key)
            if not place:
                raise validators.ValidationError("Invalid Voter ID")
