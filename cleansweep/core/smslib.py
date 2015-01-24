import urllib
from .mailer import get_queue
from ..app import app
import logging
import re

logger = logging.getLogger(__name__)


def group(values, size):
    while values:
        yield values[:size]
        values = values[size:]

class BaseSMSProvider:
    re_not_num = re.compile("[^0-9]")
    def _process_phone(number):
        if not number:
            return
        number = self.re_not_num.sub("", number)
        # remove +91
        if len(number) == 12 and number.startswith("91"):
            number = number[2:]
        return number

    def process_phone_numbers(self, phone_numbers):
        phone_numbers = [self._process_phone(phone) for phone in phone_numbers]
        return list(set(p for p in phone_numbers if p and len(p) == 10))

    def send_sms(self, phone_numbers, message):
        raise NotImplementedError()

    def send_sms_async(self, phone_numbers, message):
        q = get_queue()
        if q:
            return q.enqueue(send_sms, phone_numbers, message)
        else:
            send_sms(phone_numbers, message)

class PinacleSMSProvider(BaseSMSProvider):
    BASE_URL = "http://www.smsjust.com/blank/sms/user/urlsms.php?username={username}&pass={password}&senderid={}&message=XXXX&dest_ mobileno=XXXX&response=Y"

    def __init__(self, username, password, senderid):
        self.username = username
        self.password = password
        self.senderid = senderid

    def send_sms(self, phone_numbers, message):
        phone_numbers = ["91" + p for p in self.process_phone_numbers(phone_numbers)]
        for chunk in group(phone_numbers, 300):
            phone_numbers_txt = ",".join(chunk)
            url = sms_url.format(
                phone_numbers=urllib.quote_plus(phone_numbers_txt),
                message=urllib.quote_plus(message))
            response = urllib.urlopen(url)
            logger.info("sms response\n%s", response.read())
        return len(phone_numbers)

def get_sms_provider(provider, **kwargs):
    if provider == 'pinacle':
        return PinacleSMSProvider(**kwargs)

