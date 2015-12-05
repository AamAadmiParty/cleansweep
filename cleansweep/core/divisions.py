from ..models import Document, db

class Division(object):
	"""Division of the organization.

	Organization can be divided into multiple divisions. Each place
	in the location hierarchy will all these divisions. Volunteers can
	be assigned to a division at a place.
	"""
	type = "division"

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

	def update(self, name, description):
		"""Updates this Division object.
		"""
		self.doc.update(name=name, description=description)
		self.doc.key = name.lower().replace(" ", "-")

	def save(self):
		self.doc.save()

	def delete(self):
		self.doc.delete()

	@staticmethod
	def new():
		"""Returns a new PermissionGroup object.
		"""
		doc = Document(None, "division")
		doc.update(name="", description="")
		return Division(doc)

	@staticmethod
	def find(key):
		"""Returns the PermissionGroup with specified key.
		"""
		doc = Document.find(key, type="division")
		return doc and Division(doc)

	@staticmethod
	def all():
		"""Returns all PermissionGroup objects.
		"""
		docs = Document.search(type="division")
		return [Division(doc) for doc in docs]
