from blinker import Namespace

cleansweep = Namespace()

volunteer_signup = cleansweep.signal("volunteer-signup")
volunteer_approved = cleansweep.signal("volunteer-approved")
volunteer_rejected = cleansweep.signal("volunteer-rejected")

login_successful = cleansweep.signal("login_successful")