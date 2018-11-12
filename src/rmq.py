import pika


class RMQ:
    def __init__(self):
        self.user = 'rabbitmq'
        self.password = 'rabbitmq'
        self.host = 'localhost'
        self.port = 5672
        self.vhost = '/'
        self.exchange = 'ethereum'

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
