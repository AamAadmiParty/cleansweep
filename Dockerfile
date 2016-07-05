FROM python:2.7

ADD requirements.txt /tmp/requirements.txt
RUN pip install -r /tmp/requirements.txt

ADD . /code
WORKDIR /code
CMD gunicorn -b 0.0.0.0:5000 -w 2 cleansweep.wsgiapp:app
