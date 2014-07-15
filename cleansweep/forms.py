from flask_wtf import Form
from wtforms import StringField, SelectField
from wtforms import validators

class AddMemberForm(Form):
    name = StringField('Name', [validators.Required()])
    phone = StringField('Phone Number', [
        validators.Required(),
        validators.Regexp(r'\d{10}', message="Please enter 10 digit phone number")])
    email = StringField('Email Address', [validators.Email()])
    voterid = StringField('Voter ID')

class EditMemberForm(AddMemberForm):
    member_type = SelectField('Member Type', [validators.Required()],
        choices=("Member", "Administrator"))
