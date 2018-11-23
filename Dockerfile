FROM python:3.7

COPY requirements.pip /tmp/requirements.pip
RUN pip3 install -r /tmp/requirements.pip

COPY src /opt/application

WORKDIR /opt/application

ENV NODE_URL=https://mainnet.infura.io/v3/c5008af68e8f4de9a59f16f58a51b967
ENV WORKERS=190
#ENV HTTP_TIMEOUT=5

#ENV RANGE_FROM=47357
#ENV RANGE_TO=10
#ENV BLOCKS='[1, 2, 3]'

ENV RMQ_USER=rabbitmq
ENV RMQ_PASSWORD=rabbitmq
ENV RMQ_HOST=localhost
ENV RMQ_PORT=5672
ENV RMQ_VHOST=/
ENV RMQ_EXCHANGE=ethereum
ENV RMQ_BLOCKS_QUEUE=blocks
ENV RMQ_TRANSACTIONS_QUEUE=transactions

#ENV TIME_SLEEP=1

CMD python main.py
