from blinker import Namespace

namespace = Namespace()

add_new_volunteer = namespace.signal('add-new-volunteer')
delete_volunteer = namespace.signal('delete-volunteer')
download_volunteers_list = namespace.signal('download-volunteers-list')
