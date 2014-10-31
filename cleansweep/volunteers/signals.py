from blinker import Namespace

namespace = Namespace()

add_new_volunteer = namespace.signal('add-new-volunteer')
