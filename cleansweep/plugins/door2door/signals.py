from blinker import Namespace

namespace = Namespace()
door2door_import = namespace.signal("door2door.import")
door2door_delete = namespace.signal('delete-door2door_entry')
