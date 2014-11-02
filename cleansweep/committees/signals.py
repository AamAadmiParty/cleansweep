from blinker import Namespace

namespace = Namespace()

committee_add_member = namespace.signal("committee.add-member")
committee_remove_member = namespace.signal("committee.remove-member")
new_committee_structure = namespace.signal("committee-structure.new")
committee_structure_modified = namespace.signal("committee-structure.edit")
