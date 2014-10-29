from blinker import Namespace

namespace = Namespace()

mv_request_approved = namespace.signal('mv-request-approved')
mv_request_rejected = namespace.signal('mv-request-rejected')
