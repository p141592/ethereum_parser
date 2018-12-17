FROM python:3.7.1

COPY requirements.pip /tmp/requirements.pip
RUN pip3 install -r /tmp/requirements.pip

ENV NODE_URL=https://mainnet.infura.io/v3/c5008af68e8f4de9a59f16f58a51b967
ENV INFURA_API_KEY=c9514d7c8ec947f59b4f9e761b3d6fb3
ENV WORKERS=50
ENV DEBUG=1
#ENV HTTP_TIMEOUT=5

#ENV RANGE_FROM=666666
#ENV RANGE_TO=12000
#ENV BLOCKS='[5082714, 5082706]'

ENV RMQ_USER=rabbitmq
ENV RMQ_PASSWORD=rabbitmq
ENV RMQ_HOST=localhost
ENV RMQ_PORT=5672
ENV RMQ_VHOST=/
ENV RMQ_EXCHANGE=ethereum
ENV RMQ_BLOCKS_QUEUE=blocks
ENV RMQ_TRANSACTIONS_QUEUE=transactions
ENV RMQ_ERC20_QUEUE=ERC20
ENV APP_COMMAND=main.py
#ENV IPC_PATH=/opt/eth/data/jsonrpc.ipc
#ENV REDIS_HOST=localhost
#ENV SPEED_TEST=1

#ENV TIME_SLEEP=1

COPY src /opt/application

WORKDIR /opt/application

CMD python $APP_COMMAND
