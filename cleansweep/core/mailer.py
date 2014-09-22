from ..app import app
from envelopes import Envelope
from rq import Queue
from redis import Redis

def sendmail(to_address, subject, message, reply_to=None, cc=None, bcc=None):
    headers = {}
    if reply_to:
        headers['Reply-To'] = reply_to

    envelope = Envelope(
        from_addr=app.config['FROM_ADDRESS'],
        to_addr=to_address,
        subject=subject,
        text_body=message,
        headers=headers,
        cc_addr=cc,
        bcc_addr=bcc
    )
    server = app.config['SMTP_SERVER']
    port = app.config.get('SMTP_PORT', 25)
    username = app.config['SMTP_USERNAME']
    password = app.config['SMTP_PASSWORD']
    tls = app.config.get('SMTP_STARTTLS', False)

    envelope.send(
            host=server,
            port=port,
            login=username,
            password=password,
            tls=tls)

_q = None
def get_queue():
    global _q
    if not _q:
        host = app.config.get('REDIS_HOST')
        port = app.config.get('REDIS_PORT')
        if host and port:
            redis_conn = Redis(host, port)
            _q = Queue(connection=redis_conn) 
    return _q

def run_worker():
    from rq import Worker, Connection
    with Connection():
        q = get_queue()
        print q
        qs = [q]
        w = Worker(qs)
        w.work()

def sendmail_async(*a, **kw):
    q = get_queue()
    if q:
        return q.enqueue(sendmail, *a, **kw)
    else:
        sendmail(*a, **kw)