from ..main import app
from ..models import db, Place, PlaceType, Member, Document
from .. import helpers as h
from .test_models import DBTestCase
from flask import session

class AppTestCase(DBTestCase):
    def setUp(self):
        DBTestCase.setUp(self)
        self.app = app.test_client()

        t = PlaceType("STATE", "STATE", 10)
        db.session.add(t)

        p = Place("DL", "Delhi", t)
        db.session.add(p)
        p.add_member('Test User', 'test@example.com', '9876500012')
        db.session.commit()

        # monkey-patch get permissions
        self.old_get_permissions = h.get_permissions
        self.old_get_current_user = h.get_current_user
        h.get_permissions = self._get_permissions
        h.get_current_user = self._get_current_user

        app.before_request_funcs[None].append(self._before_request)

    def tearDown(self):
        h.get_permissions = self.old_get_permissions
        h.get_current_user = self.old_get_current_user
        DBTestCase.tearDown(self)      
        app.before_request_funcs[None].remove(self._before_request)

    def _before_request(self):
        session['user'] = 'test@example.com'

    def _get_permissions(self, user, place):
        return ['*']

    def _get_current_user(self):
        return Member.find(email='test@example.com')

class AppTest(AppTestCase):
    def assertResponseContains(self, url, substring):
        r = self.app.get(url)
        self.assertTrue(substring in r.data)

    def test_dashboard(self):
        self.assertResponseContains("/dashboard", "Dashboard")

    def test_place(self):
        self.assertResponseContains("/DL", "Delhi")

    def test_admin(self):
        self.assertResponseContains("/admin", "Admin Center")
        self.assertResponseContains("/admin/permission-groups", "Permission Groups")
        self.assertResponseContains("/admin/committee-structures", "Committee Structures")

    def test_volunteers(self):
        self.assertResponseContains("/DL/volunteers", "Volunteers")
        self.assertResponseContains("/DL/volunteers", "test@example.com")
        self.assertResponseContains("/DL/volunteers/add", "Add Volunteer")
