from flask.ext.testing import TestCase
from ..main import app
from ..models import db, Place, PlaceType, Member, Document
from ..plugins.committees.models import CommitteeType

class DBTestCase(TestCase):
    setup_place_types = False
    setup_places = False

    def create_app(self):
        return app

    def add_place_types(self):
        def add(name, short_name, level):
            t = PlaceType(name, short_name, level)
            db.session.add(t)
            return t

        self.STATE = add('State', 'STATE', 10)
        self.REGION = add('Region', 'REGION', 20)
        self.LC = add('Loksabha Constituency', 'LC', 30)
        self.AC = add('Assembly Constituency', 'AC', 40)
        self.WARD = add('Ward', 'WARD', 50)
        db.session.commit()

    def add_places(self):
        self.KA = self.add_place("KA", "Karnataka", self.STATE)
        self.LC01 = self.add_place("KA/LC01", "Bangalore South", self.LC, parent=self.KA)
        self.AC001 = self.add_place("KA/AC001", "Jayanagar", self.AC, parent=self.LC01)
        self.W001 = self.add_place("KA/AC001/W001", "Jayanagar East", self.WARD, parent=self.AC001)

    def add_place(self, key, name, type, parent=None):
        """Adds and returns a place with given info. 

        Used by testcases for creating a test place.
        """
        p = Place(key, name, type)
        if parent:
            parent.add_place(p)
        else:
            db.session.add(p)
        db.session.commit()
        return p        

    def setUp(self):
        db.create_all()
        if self.setup_place_types:
            self.add_place_types()

        if self.setup_places:
            self.add_places()

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
    setup_place_types = True

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

    def test_get_siblings(self):
        KA = self.add_place("KA", "Karnataka", self.STATE)
        self.assertEquals(KA.get_siblings(), [KA])

        LC24 = self.add_place('KA/LC24', 'Bangalore North', self.LC, parent=KA)
        LC25 = self.add_place('KA/LC25', 'Bangalore Central', self.LC, parent=KA)
        LC26 = self.add_place('KA/LC25', 'Bangalore South', self.LC, parent=KA)
        self.assertEquals(LC24.get_siblings(), [LC24, LC25, LC26])

    def test_iparent(self):
        KA = self.add_place("KA", "Karnataka", self.STATE)
        LC24 = self.add_place('KA/LC24', 'Bangalore North', self.LC, parent=KA)
        AC158 = self.add_place('KA/AC158', 'Hebbal', self.AC, parent=LC24)
        self.assertEquals(KA.iparent, None)
        self.assertEquals(LC24.iparent, KA)
        self.assertEquals(AC158.iparent, LC24)

    def test_search_members(self):
        KA = self.add_place("KA", "Karnataka", self.STATE)
        KA.add_member("Evalu Ator", "eval@ator.com", "0001234500")
        db.session.commit()

        result = list(KA.search_members("Eval"))
        assert len(result) == 1
        assert result[0].name == 'Evalu Ator'

        result = list(KA.search_members("Foo"))
        assert len(result) == 0

    def test_search_all_members(self):
        KA = self.add_place("KA", "Karnataka", self.STATE)
        KA.add_member("Evalu Ator", "eval@ator.com", "0001234500")
        db.session.commit()

        result = KA.search_all_members("Ator")
        assert len(result) == 1
        assert result[0].phone == "0001234500"

        result = KA.search_all_members("0001234500")
        assert len(result) == 1
        assert result[0].email == "eval@ator.com"

        result = KA.search_all_members("eval@ator.com")
        assert len(result) == 1
        assert result[0].name == "Evalu Ator"

        result = KA.search_all_members("asdf")
        assert len(result) == 0


class MemberTest(DBTestCase):
    setup_place_types = True

    def setUp(self):
        DBTestCase.setUp(self)
        self.place = self.add_place("KA", "Karnataka", self.STATE)

    def add_member(self, name, email, phone="1234567890"):
        m = self.place.add_member(name=name, email=email, phone=phone)
        db.session.commit()
        return m

    def test_member_create(self):
        m = self.add_member(name="Alice", email="alice@example.com")
        self.assertEquals(m.place, self.place)
        self.assertEquals(self.place.members.all(), [m])

    def test_find(self):
        m = self.add_member(name="Alice", email="alice@example.com")
        m2 = Member.find(email='alice@example.com')
        self.assertTrue(m2 is not None)
        self.assertEquals(m, m2)

    def test_find_case_sensitive(self):
        m = self.add_member(name="Alice", email="alice@example.com")
        m2 = Member.find(email='Alice@example.com')
        self.assertTrue(m2 is not None)
        self.assertEquals(m, m2)

class CommitteeTypeTest(DBTestCase):
    setup_place_types = True
    setup_places = True

    def test_committee_type(self):
        t = CommitteeType(self.KA, self.LC, "Political Action Committee", "xxx", "pac")
        db.session.add(t)
        db.session.commit()
        self.assertTrue(t.id is not None)
        self.assertTrue(self.KA.committee_types.all(), [t])

    def test_committee_role(self):
        t = CommitteeType(self.KA, self.LC, "Political Action Committee", "xxx", "pac")
        db.session.add(t)
        db.session.commit()

        t.add_role("Convener", False, "read,write")
        t.add_role("Co-convener", False, "read,write")
        t.add_role("Member", True, "read")
        db.session.commit()

        t2 = self.KA.committee_types.first()

        def assert_role(role, name, multiple, permission):
            self.assertEquals(role.role, name)
            self.assertEquals(role.multiple, multiple)
            self.assertEquals(role.permission, permission)

        assert_role(t2.roles[0], 'Convener', False, "read,write")
        assert_role(t2.roles[1], 'Co-convener', False, "read,write")
        assert_role(t2.roles[2], 'Member', True, "read")

    def test_find(self):
        t = CommitteeType(self.KA, self.LC, "Political Action Committee", "xxx", "pac")
        db.session.add(t)
        db.session.commit()

        t2 = CommitteeType.find(self.KA, "pac")
        self.assertTrue(t2 is not None)
        self.assertEquals(t.id, t2.id)

        # should be None because the committee_type is defined for LC, not STATE
        t2 = CommitteeType.find(self.KA, "pac", recursive=True)
        self.assertTrue(t2 is None)

        t2 = CommitteeType.find(self.LC01, "pac", recursive=True)
        self.assertTrue(t2 is not None)
        self.assertEquals(t.id, t2.id)

        # should be None again because of place_type mismatch.
        t2 = CommitteeType.find(self.AC001, "pac", recursive=True)
        self.assertTrue(t2 is None)

    def test_get_committee(self):
        # Tests Place.get_committee
        t = CommitteeType(self.KA, self.LC, "Political Action Committee", "xxx", "pac")
        db.session.add(t)
        db.session.commit()

        c = self.KA.get_committee("pac")
        self.assertTrue(c is None)

        c = self.LC01.get_committee("pac")
        self.assertTrue(c is not None)
        self.assertTrue(c.id is None) # new committee

        c = self.AC001.get_committee("pac")
        self.assertTrue(c is None)

    def test_find_all(self):
        t1 = CommitteeType(self.KA, self.LC, "Test LC committee", "xxx", "test-lc")
        db.session.add(t1)

        t2 = CommitteeType(self.KA, self.AC, "Test AC Committee", "xxx", "test-ac")
        db.session.add(t2)
        db.session.commit()

        x = CommitteeType.find_all(self.KA, all_levels=True)
        self.assertEquals(x, [t1, t2])

        x = CommitteeType.find_all(self.LC01, all_levels=True)
        self.assertEquals(x, [t1, t2])

        x = CommitteeType.find_all(self.AC001, all_levels=True)
        self.assertEquals(x, [t2])

    def get_test_stats(self):
        t1 = CommitteeType(self.KA, self.LC, "Test LC committee", "xxx", "test-lc")
        db.session.add(t1)
        db.session.commit()

        LC02 = self.add_place("KA/LC02", "R T Nagar", self.LC, parent=self.KA)


        self.assertEquals(t1.get_stats(self.KA), {
            "num_roles": 0,
            "committees_defined": 0,
            "total_members": 0,
            "total_places": 2
            })

        self.assertEquals(t1.get_stats(self.LC01), {
            "num_roles": 0,
            "committees_defined": 0,
            "total_members": 0,
            "total_places": 1
            })

class DocumentTest(DBTestCase):
    def new_doc(self, _key, type, **kw):
        doc = Document(_key, type)
        doc.update(**kw)
        doc.save()
        return doc

    def test_new_document(self):
        data = {
            "name": "foo",
            "email": "foo@example.com",
            "list": [1, 2, 3]
        }
        doc = self.new_doc("foo", type="test-type", **data)

        assert doc.key == "foo"
        assert doc.type == "test-type"

        doc2 = Document.find("foo")
        assert doc2.key == "foo"
        assert doc2.type == "test-type"
        assert doc2.data == data

    def test_search(self):
        a1 = self.new_doc("a1", type="a", name='a1')
        a2 = self.new_doc("a2", type="a", name='a2')
        b1 = self.new_doc("b1", type="b", name='b1')

        docs = Document.search(type='a')
        assert [doc.key for doc in docs] == ['a1', 'a2']

        docs = Document.search(type='a', name='a1')
        assert [doc.key for doc in docs] == ['a1']

        docs = Document.search(type='b')
        assert [doc.key for doc in docs] == ['b1']

    def test_save(self):
        a1 = self.new_doc("a1", type="a", name='a1')
        a1.update(name="aa11")
        a1.save()

        doc = Document.find("a1")
        assert a1.data['name'] == "aa11"

    def test_delete(self):
        a1 = self.new_doc("a1", type="a", name='a1')
        a2 = self.new_doc("a2", type="a", name='a2')
        a1.delete()

        assert Document.find("a1") is None

        docs = Document.search(type="a")
        assert [doc.key for doc in docs] == ['a2']

    def test_new_key(self):
        a1 = self.new_doc(None, type="a", name='a1')
        a1.save()

        assert a1.key is not None
        assert Document.find(a1.key) is not None


if __name__ == '__main__':
    import unittest
    unittest.main()