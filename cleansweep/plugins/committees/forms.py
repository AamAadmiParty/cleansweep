from flask_wtf import Form
import wtforms
from wtforms import FieldList, FormField, SelectField, StringField, TextAreaField, HiddenField
from wtforms import validators
from ...models import db
from . models import CommitteeType, CommitteeRole
from ...core.permissions import PermissionGroup

class RoleForm(wtforms.Form):
    # Extending from wtforms.Form instead of flask_wtf.Form as this adds
    # unnecessary CSRF token even this is an inner form.
    # Source: http://stackoverflow.com/a/15651474/189776

    role_id = HiddenField()
    name = StringField('Name')
    multiple = SelectField('Multiple?', choices=[("no", "One Member"), ("yes", "Multiple Members")], default='no')
    permission = SelectField('Permissions', choices=[])

    def __init__(self, *a, **kw):
        wtforms.Form.__init__(self, *a, **kw)
        groups = PermissionGroup.all()
        self.permission.choices = [(g.key, g.name) for g in groups]

class NewCommitteeForm(Form):
    committee_type_id = HiddenField()
    name = StringField('Name', [validators.Required()])
    slug = StringField('Slug', [validators.Required()])
    level = SelectField('Level', choices=[])
    description = TextAreaField('Description', [])
    roles = FieldList(FormField(RoleForm), min_entries=0)

    def __init__(self, place, *a, **kw):
        Form.__init__(self, *a, **kw)
        self.place = place
        place_types = [place.type] + place.type.get_subtypes()
        self.level.choices = [(t.short_name, t.name) for t in place_types]
        self.ensure_empty_slots()

    def validate_slug(self, field):
        # When editing an existing committee type
        if self.committee_type_id.data:
            ct = CommitteeType.query.filter_by(id=self.committee_type_id.data).first()
            # if the slug is not modified
            if ct.slug == field.data:
                return

        if CommitteeType.find(self.place, field.data):
            raise validators.ValidationError("There is already a committee in {} with same slug.".format(self.place.key))

    def ensure_empty_slots(self, n=5):
        # Ensure that there are at least 5 empty slots
        empty_slots = sum(1 for role in self.data['roles'] if not role['name'].strip())
        for i in range(n-empty_slots):
            self.roles.append_entry()

    def load(self, committee_structure):
        c = committee_structure
        self.committee_type_id.data = c.id
        self.name.data = c.name
        self.slug.data = c.slug
        self.level.data = c.place_type.short_name
        self.description.data = c.description
        roles = [dict(role_id=role.id, name=role.role, multiple=['no', 'yes'][role.multiple], permission=role.permission) for role in c.roles]
        self.roles.process(None, roles)
        self.ensure_empty_slots()

    def save(self, committee_structure):
        c = committee_structure

        c.name = self.name.data
        c.slug = self.slug.data
        c.description = self.description.data
        for roledata in self.data['roles']:
            if roledata.get('role_id'):
                role = CommitteeRole.query.filter_by(id=roledata['role_id']).first()
                role.role = roledata['name']
                role.multiple = roledata['multiple'] == 'yes'
                role.permission = roledata['permission']
                db.session.add(role)
            elif roledata.get('name') and roledata.get('name').strip():
                c.add_role(
                    roledata['name'],
                    roledata['multiple'] == 'yes',
                    roledata['permission'])
        db.session.add(c)
