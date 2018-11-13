import os

import pika

e = os.environ.get


class RMQ:
    def __init__(self):
        self.user = e('RMQ_USER', 'rabbitmq')
        self.password = e('RMQ_PASSWORD', 'rabbitmq')
        self.host = e('RMQ_HOST', 'localhost')
        self.port = int(e('RMQ_PORT', 5672))
        self.vhost = e('RMQ_VHOST', '/')
        self.exchange = e('RMQ_EXCHANGE', 'ethereum')

    def __enter__(self):
        credentials = pika.PlainCredentials(self.user, self.password)
        parameters = pika.ConnectionParameters(self.host,
                                               self.port,
                                               self.vhost,
                                               credentials)

        self.conn = pika.BlockingConnection(parameters=parameters)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.conn.close()
        if exc_val:
            raise BaseException

    def send_data(self, data, routing_key):
        channel = self.conn.channel()
        channel.basic_publish(
            exchange=self.exchange,
            routing_key=routing_key,
            body=str(data)
        )


def send_data(data, routing_key):
    with RMQ() as rmq:
        rmq.send_data(data, routing_key)
