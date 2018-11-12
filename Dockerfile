FROM python:3.7

COPY requirements.pip /tmp/requirements.pip
RUN pip3 install -r /tmp/requirements.pip

COPY src /opt/application

CMD python /opt/application/aio_read_history.py