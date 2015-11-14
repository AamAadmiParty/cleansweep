from blinker import Namespace

namespace = Namespace()

volunteer_signup = namespace.signal('volunteer-signup')
volunteer_signup_approved = namespace.signal('volunteer-signup-approved')
volunteer_signup_rejected = namespace.signal('volunteer-signup-rejected')
