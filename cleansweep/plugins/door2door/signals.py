from blinker import Namespace

namespace = Namespace()
door2door_import = namespace.signal("door2door.import")
