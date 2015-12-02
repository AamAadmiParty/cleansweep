"""Permission support for cleansweep.

Maintains the registry of permissions across all various plugins 
and provides framework for managing permission groups.

Each plugin defines all the permissions it want to provide by calling 
define_permission function.

	define_permission(
		name="volunteers.add",
		description="Permission to add new volunteers")

Permisison Groups are created from the admin center of the website and they
are used to specify permissions for various roles.
"""
from collections import namedtuple
from ..models import Document, db

Permission = namedtuple("Permission", "name, description")

_permission_registry = {}

def define_permission(name, description=""):
	"""Defines a new permission.
	"""
	_permission_registry[name] = Permission(name, description)

def get_all_permissions():
	return sorted(_permission_registry.values(), key=lambda p: p.name)


class PermissionGroup(object):
	"""PermissionGroup is a collection of permissions.

	PermissionGroup is used to attach a group of permissions to a role.
	It is implemented using simple document store, see Document class in models.
	"""
	type = "permission-group"

	def __init__(self, doc):
		self.doc = doc

	@property
	def key(self):
		return self.doc.key

	@property
	def data(self):
		return self.doc.data

	@property
	def name(self):
		return self.doc.data['name']

	@property
	def description(self):
		return self.doc.data['description']

	@property
	def permissions(self):
		plist = self.doc.data['properties']
		return [_permission_registry[p] for p in plist if p in _permission_registry]

	def update(self, name, description, permissions):
		"""Updates this PermissionGroup object.

		Please note that permissions is a list of permission names, not permission objects.
		"""
		self.doc.update(name=name, description=description, permissions=permissions)

	def save(self):
		self.doc.save()

	def delete(self):
		self.doc.delete()

	@staticmethod
	def new():
		"""Returns a new PermissionGroup object.
		"""
		doc = Document(None, "permission-group")
		doc.update(name="", description="", properties=[])
		return PermissionGroup(doc)

	@staticmethod
	def find(key):
		"""Returns the PermissionGroup with specified key.
		"""
		doc = Document.find(key, type="permission-group")
		return doc and PermissionGroup(doc)

	@staticmethod
	def all():
		"""Returns all PermissionGroup objects.
		"""
		docs = Document.search(type="permission-group")
		return [PermissionGroup(doc) for doc in docs]
