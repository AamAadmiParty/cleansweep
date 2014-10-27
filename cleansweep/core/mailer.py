from ..app import app
from envelopes import Envelope
from rq import Queue
from redis import Redis
import pynliner
import logging
from ..models import Unsubscribe

logger = logging.getLogger(__name__)

class Message:
    def __init__(self, to_addr=None, subject=None, reply_to=None):
        self.to_addr = to_addr
        self.subject = subject
        self.reply_to = None
        self.text_body = None
        self.html_body = None

    def set_subject(self, subject):
        self.subject = subject
        return ""

    def send(self):
        sendmail(
            to_address=self.to_addr, 
            subject=self.subject,
            message=self.text_body,
            message_html=self.html_body,
            reply_to=self.reply_to)

    def send_async(self):
        sendmail_async(
            to_address=self.to_addr, 
            subject=self.subject,
            message=self.text_body,
            message_html=self.html_body,
            reply_to=self.reply_to)

def sendmail(to_address, subject, message, message_html=None, reply_to=None, cc=None, bcc=None):
    headers = {}
    if reply_to:
        headers['Reply-To'] = reply_to

    if message_html:
        message_html = pynliner.fromString(message_html)

    if Unsubscribe.contains(to_address):
        logger.warn("%s is in the unsubscribed list. Not sending email.", to_address)
        return

    envelope = Envelope(
        from_addr=app.config['FROM_ADDRESS'],
        to_addr=to_address,
        subject=subject,
        text_body=message,
        html_body=message_html,
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
        qs = [q]
        w = Worker(qs)
        w.work()

def sendmail_async(*a, **kw):
    q = get_queue()
    if q:
        return q.enqueue(sendmail, *a, **kw)
    else:
        sendmail(*a, **kw)