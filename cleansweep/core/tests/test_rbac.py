from .. import rbac

class TestRBAC:
    def setup_method(self, method):
        rbac._role_providers = []
        rbac._permission_providers = []

    def test_get_user_roles(self):
        roles = {
            "alice": [{"role": "role1", "place": "place1"}],
            "bob": [{"role": "role2", "place": "place2"}],
        }
        @rbac.role_provider
        def get_roles(user):
            return roles.get(user, [])

        assert rbac.get_user_roles("alice") == [{"role": "role1", "place": "place1"}]
        assert rbac.get_user_roles("bob") == [{"role": "role2", "place": "place2"}]
        assert rbac.get_user_roles("david") == []

    def test_get_user_roles_with_multiple_providers(self):
        @rbac.role_provider
        def alice_roles(user):
            if user == "alice":
                return [{"role": "role1", "place": "place1"}]
            else:
                return []

        @rbac.role_provider
        def bob_roles(user):
            if user == "bob":
                return [{"role": "role2", "place": "place2"}]
            else:
                return []

        assert rbac.get_user_roles("alice") == [{"role": "role1", "place": "place1"}]
        assert rbac.get_user_roles("bob") == [{"role": "role2", "place": "place2"}]
        assert rbac.get_user_roles("david") == []

    def test_get_user_permissions(self):
        @rbac.role_provider
        def simple_roles(user):
            return [{"role": "role1", "place": "place1"}]

        @rbac.permission_provider
        def simple_perms(role):
            return [{"place": "place1", "permission": "add-volunteer"}]

        user = "alice"
        assert rbac.get_user_permissions(user) == [{"place": "place1", "permission": "add-volunteer"}]

    def test_can(self, monkeypatch):
        def mock_get_user_permissions(user):
            if user == "alice":
                return [{"place": "DL/AC001", "permission": "send-email"}]
            elif user == "bob":
                return [{"place": "DL/AC002", "permission": "add-volunteer"}]

        monkeypatch.setattr(rbac, "get_user_permissions", mock_get_user_permissions)

        AC001 = MockPlace("DL/AC001", ["DL", "DL/DT01"])
        AC001_PB0001 = MockPlace("DL/AC001/PB0001", ["DL", "DL/DT01", "DL/AC001"])
        AC002 = MockPlace("DL/AC002", ["DL", "DL/DT02"])
        AC002_PB0001 = MockPlace("DL/AC002/PB0001", ["DL", "DL/DT02", "DL/AC002"])

        assert rbac.can("alice", "send-email", AC001)
        assert rbac.can("alice", "send-email", AC001_PB0001)
        assert not rbac.can("alice", "send-email", AC002)
        assert not rbac.can("alice", "add-volunteer", AC001)

        assert rbac.can("bob", "add-volunteer", AC002)
        assert rbac.can("bob", "add-volunteer", AC002_PB0001)
        assert not rbac.can("bob", "add-volunteer", AC001)
        assert not rbac.can("bob", "send-email", AC002)

class MockPlace:
    def __init__(self, key, parents):
        self.key = key
        self.parents = [MockPlace(k, []) for k in parents]

    def __repr__(self):
        return "<MockPlace({})>".format(self.key)

def testMockPlace():
    place = MockPlace("DL/AC001", ["DL", "DL/DT01"])
    assert place.key == "DL/AC001"
    assert [p.key for p in place.parents] == ["DL", "DL/DT01"]
