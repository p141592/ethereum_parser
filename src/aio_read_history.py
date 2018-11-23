import asyncio
import os
import time
import ujson

import aio_pika
import aiohttp

from data import get_blocks_count, prepare_data

start = time.time()
e = os.environ.get


def block_number_generator(_from, _to):
    for number in range(int(_from), int(_to)):
        yield number


@prepare_data
async def fetch(session, method, params):
    data = {"jsonrpc": "2.0", "method": method, "params": params, "id": 1}
    async with session.post(
            'https://mainnet.infura.io/v3/c5008af68e8f4de9a59f16f58a51b967',
            json=data,
            headers={'Content-Type': 'application/json'},
            timeout=aiohttp.ClientTimeout(total=e('HTTP_TIMEOUT', 5))
    ) as response:
        return await response.text()


async def main(loop, _from=0, _to=get_blocks_count()):
    generator = block_number_generator(_from, _to)
    connection = await aio_pika.connect_robust(
        f"amqp://{e('RMQ_USER', 'rabbitmq')}:{e('RMQ_PASSWORD', 'rabbitmq')}@{e('RMQ_HOST', 'localhost')}/",
        loop=loop
    )

    channel = await connection.channel()
    async with aiohttp.ClientSession(json_serialize=ujson.dumps) as session:
        while 1:
            try:
                number = next(generator)
                block = await fetch(session, 'eth_getBlockByNumber', [hex(number), False])
                if block:
                    await channel.default_exchange.publish(
                        aio_pika.Message(
                            body=str(block).encode()
                        ),
                        routing_key=e('RMQ_BLOCKS_QUEUE', 'blocks')
                    )

                    for transaction_hash in block.get('transactions', []):
                        data = await fetch(session, 'eth_getTransactionByHash', [transaction_hash])
                        if data:
                            await channel.default_exchange.publish(
                                aio_pika.Message(
                                    body=str(data).encode()
                                ),
                                routing_key=e('RMQ_TRANSACTIONS_QUEUE', 'transactions')
                            )
            except StopIteration:
                break

        await connection.close()


def run():
    _from = 0
    number = get_blocks_count()
    workers_len = int(e('WORKERS', 80))
    pre_length = number/workers_len

    ioloop = asyncio.get_event_loop()

    workers = []
    for name in range(workers_len):
        workers.append(ioloop.create_task(main(ioloop, _from=_from, _to=_from+int(pre_length))))
        _from = _from + int(pre_length)

    wait_tasks = asyncio.wait(workers)

    ioloop.run_until_complete(wait_tasks)
    ioloop.close()


if __name__ == '__main__':
    run()
    print(f'DURATION: {start-time.time()}')
