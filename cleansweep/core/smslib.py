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

    # separator for specifying multiple phone numbers.
    # Right now , and / are supported.
    re_sep = re.compile("[,/]")

    def _process_phone(self, number):
        if not number:
            return

        # take first number when there are multiple
        number = self.re_sep.split(number)[0]

        number = self.re_not_num.sub("", number)
        # remove +91
        if len(number) == 12 and number.startswith("91"):
            number = number[2:]
        return number

    def process_phone_numbers(self, phone_numbers):
        phone_numbers = [self._process_phone(phone) for phone in phone_numbers]
        for p in phone_numbers:
            if p and len(p) != 10:
                logger.warn("Bad phone number %s, ignoring...", p)
        return list(set(p for p in phone_numbers if p and len(p) == 10))

    def send_sms(self, phone_numbers, message):
        raise NotImplementedError()

    def send_sms_async(self, phone_numbers, message):
        q = get_queue()
        if q:
            return q.enqueue(self.send_sms, phone_numbers, message)
        else:
            self.send_sms(phone_numbers, message)

class GenericSMSProvider(BaseSMSProvider):
    URL_TEMPLATE = None

    def __init__(self, **kwargs):
        self.parameters = kwargs

    def get_url_template(self):
        # take URL template from the object or from the parameters
        return self.URL_TEMPLATE or self.parameters['url']

    def send_sms(self, phone_numbers, message):
        phone_numbers = ["91" + p for p in self.process_phone_numbers(phone_numbers)]
        logger.info("sending sms to %s phone numbers.", len(phone_numbers))

        url_template = self.get_url_template()

        for chunk in group(phone_numbers, 300):
            phone_numbers_txt = ",".join(chunk)
            d = dict(self.parameters,
                phone_numbers=phone_numbers_txt,
                message=message)
            d = {k: urllib.quote_plus(v) for k, v in d.items()}
            url = url_template.format(**d)
            logger.info("sending sms using URL: %s", url)
            response = urllib.urlopen(url)
            logger.info("sms response\n%s", response.read())
        return len(phone_numbers)

class PinacleSMSProvider(GenericSMSProvider):
    URL_TEMPLATE = "http://www.smsjust.com/blank/sms/user/urlsms.php?username={username}&pass={password}&senderid={senderid}&message={message}&dest_mobileno={phone_numbers}&response=Y"

class SMSCuppaProvider(GenericSMSProvider):
    TRANS_URL_TEMPLATE = "http://trans.smscuppa.com/sendsms.jsp?user={username}&password={password}&mobiles={phone_numbers}&sms={message}&senderid={senderid}&version=3"
    PROMO_URL_TEMPLATE = "http://mtrans.smscuppa.com/sendsms.jsp?user={username}&password={password}&mobiles={phone_numbers}&sms={message}&senderid={senderid}&version=3"

    def get_url_template(self):
        if self.parameters.get("mode") == "transactional":
            return self.TRANS_URL_TEMPLATE
        else:
            return self.PROMO_URL_TEMPLATE

def get_sms_provider(provider, **kwargs):
    if provider == 'pinacle':
        return PinacleSMSProvider(**kwargs)
    elif provider == 'smscuppa':
        return SMSCuppaProvider(**kwargs)
    else:
        return GenericSMSProvider(**kwargs)

