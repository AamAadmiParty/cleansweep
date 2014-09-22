import urllib
from .mailer import get_queue
from ..app import app
import logging
import re

logger = logging.getLogger(__name__)

re_not_num = re.compile("[^0-9]")
def process_phone(number):
    if not number:
        return
    number = re_not_num.sub("", number)
    # remove +91
    if len(number) == 12 and number.startswith("91"):
        number = number[2:]
    return number

def group(values, size):
    while values:
        yield values[:size]
        values = values[size:]

def send_sms(phone_numbers, message):
    sms_url = app.config['SMS_URL']

    phone_numbers = [process_phone(phone) for phone in phone_numbers]   
    phone_numbers = list(set(p for p in phone_numbers if p and len(p) == 10))

    for chunk in group(phone_numbers, 300):
        phone_numbers_txt = ",".join(chunk)
        url = sms_url.format(
            phone_numbers=urllib.quote_plus(phone_numbers_txt), 
            message=urllib.quote_plus(message))
        response = urllib.urlopen(url)
        logger.info("sms response\n%s", response.read())
    return len(phone_numbers)

def send_sms_async(phone_numbers, message):
    q = get_queue()
    if q:
        return q.enqueue(send_sms, phone_numbers, message)
    else:
        send_sms(phone_numbers, message)