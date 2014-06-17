from flask.ext.testing import TestCase

from ..app import app
from ..models import db, Place, PlaceType


class DBTestCase(TestCase):
    def create_app(self):     
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'   
        return app

    def setUp(self):
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()

class PlaceTypeTest(DBTestCase):
    def testPlaceType(self):
        t1 = PlaceType("State", "STATE", 20)
        db.session.add(t1)
        db.session.commit()

        t = PlaceType.get("STATE")
        self.assertEquals(t.name, 'State')
        self.assertEquals(t.level, 20)

class PlaceTest(DBTestCase):
    def setUp(self):
        DBTestCase.setUp(self)

        def add(name, short_name, level):
            t = PlaceType(name, short_name, level)
            db.session.add(t)
            return t

        self.STATE = add('State', 'STATE', 10)
        self.REGION = add('Region', 'REGION', 20)
        self.LC = add('Loksabha Constituency', 'LC', 30)
        db.session.commit()

    def test_create(self):
        p = Place('KA', 'Karnataka', self.STATE)
        db.session.add(p)
        db.session.commit()

        ka = Place.find('KA')
        self.assertTrue(ka is not None)
        self.assertEquals(ka.key, 'KA')
        self.assertEquals(ka.name, 'Karnataka')
        self.assertEquals(ka.type.name, 'State')
        self.assertEquals(ka.parents, [])

    def test_add_place(self):
        KA = Place('KA', 'Karnataka', self.STATE)
        db.session.add(KA)
        db.session.commit()

        R01 = Place('KA/R01', 'Bangalore Region', self.REGION)
        KA.add_place(R01)

        LC24 = Place('KA/LC24', 'Bangalore North', self.LC)
        KA.add_place(LC24)

        LC26 = Place('KA/LC26', 'Bangalore South', self.LC)
        KA.add_place(LC26)
        db.session.commit()

        self.assertEquals(KA.get_places(), [LC24, LC26, R01])
        self.assertEquals(KA.get_places(type=self.REGION), [R01])
        self.assertEquals(KA.get_places(type=self.LC), [LC24, LC26])

    def add_place(self, key, name, type, parent=None):
        p = Place('KA', 'Karnataka', self.STATE)
        if parent:
            parent.add_place(p)
        else:
            db.session.add(p)
        db.session.commit()
        return p

    def test_get_siblings(self):
        KA = self.add_place("KA", "Karnataka", self.STATE)
        self.assertEquals(KA.get_siblings(), [KA])

        LC24 = self.add_place('KA/LC24', 'Bangalore North', self.LC, parent=KA)
        LC25 = self.add_place('KA/LC25', 'Bangalore Central', self.LC, parent=KA)
        LC26 = self.add_place('KA/LC25', 'Bangalore South', self.LC, parent=KA)
        self.assertEquals(LC24.get_siblings(), [LC24, LC25, LC26])

if __name__ == '__main__':
    import unittest
    unittest.main()