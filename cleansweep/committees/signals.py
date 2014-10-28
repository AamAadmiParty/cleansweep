from blinker import Namespace

namespace = Namespace()

committee_add_member = namespace.signal("committee.add-member")
committee_remove_member = namespace.signal("committee.remove-member")