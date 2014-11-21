from flask_wtf import Form
import wtforms
from wtforms import FieldList, FormField, SelectField, StringField, TextAreaField, HiddenField
from wtforms import validators
from . import models
from .voterlib import voterdb

class AddMemberForm(Form):
    name = StringField('Name', [validators.Required()])
    phone = StringField('Phone Number', [
        validators.Required(), 
        validators.Regexp(r'\d{10}', message="Please enter 10 digit phone number")])
    email = StringField('Email Address', [validators.Email()])
    voterid = StringField('Voter ID')

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
        if not self.voterid.data and not self.place.data:
            raise validators.ValidationError("You must provide either a valid voter ID or locality.")

        if self.voterid.data:
            voterid = self.voterid.data
            voterinfo = voterdb.get_voter(voterid=voterid)
            if not voterinfo:
                raise validators.ValidationError("Invalid Voter ID")

class AddVolunteerForm(SignupForm):
    email = StringField('Email Address', [validators.Email()])

    def __init__(self, place, *a, **kw):
        SignupForm.__init__(self, *a, **kw)
        self._place = place

    def validate_email(self, field):
        email = field.data
        if models.PendingMember.find(email=email) or models.Member.find(email=email):
            raise validators.ValidationError('This email address is already used')

    def validate_voterid(self, field):
        SignupForm.validate_voterid(self, field)
        if self.voterid.data:
            voterid = self.voterid.data
            voterinfo = voterdb.get_voter(voterid=voterid)
            if voterinfo and not voterinfo.get_place().has_parent(self._place):
                raise validators.ValidationError("This voter ID doesn't belong to the current place.")

    def validate_locality(self, field):
        if not self.place.data:
            return
        p = models.Place.find(key=self.place.data)
        if not p:
            raise validators.ValidationError('Unable to identify this locality.')
        if not p.has_parent(self._place):
            raise validators.ValidationError("Sorry, the specified location is not outside the current region.")

class SendMailForm(Form):
    people = SelectField('Send Email to',
                choices=[
                    ('self', 'Just Me (for testing)'),
                    ('volunteers', 'All Volunteers'),
                    ('contacts', 'All Contacts')                    
                ])
    subject = StringField('Subject', validators=[validators.Required()])
    message = TextAreaField("Message", validators=[validators.Required()])


class SendSMSForm(Form):
    people = SelectField('Send SMS to',
                choices=[
                    ('self', 'Just Me (for testing)'),
                    ('volunteers', 'All Volunteers'),
                    ('contacts', 'All Contacts')
                ])
    message = TextAreaField("Message", validators=[validators.Required()])

class UnsubscribeForm(Form):
    email = StringField('Email Address', [validators.Email()])
