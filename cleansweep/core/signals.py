from blinker import Namespace

cleansweep = Namespace()

def make_signal(name):
	return cleansweep.signal(name)

volunteer_signup = cleansweep.signal("volunteer-signup")
volunteer_approved = cleansweep.signal("volunteer-approved")
volunteer_rejected = cleansweep.signal("volunteer-rejected")

login_successful = cleansweep.signal("login_successful")