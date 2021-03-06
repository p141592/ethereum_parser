import asyncio
import os
import sys
import time
import ujson
import rapidjson as json
import aio_pika
import aiohttp

from data import get_blocks_count, prepare_data
from erc20 import decode_contract_data

start = time.time()
e = os.environ.get

_LEN = 0


def block_number_generator(_from, _to):
    for number in range(int(_from), int(_to)) if not e('BLOCKS') else json.loads(e('BLOCKS')):
        yield number


generator = block_number_generator(int(e('RANGE_FROM', 0)), int(e('RANGE_TO', get_blocks_count())))


@prepare_data
async def fetch(session, method, params):
    global _LEN
    data = {"jsonrpc": "2.0", "method": method, "params": params, "id": 1}
    async with session.post(
            'https://mainnet.infura.io/v3/c5008af68e8f4de9a59f16f58a51b967',
            json=data,
            headers={'Content-Type': 'application/json'},
            timeout=aiohttp.ClientTimeout(total=e('HTTP_TIMEOUT', 5))
    ) as response:
        _LEN += 1
        return await response.text()


async def parse_block(channel, session, queue, number):
    block = await fetch(session, 'eth_getBlockByNumber', [hex(number), False])

    if block:
        await channel.default_exchange.publish(
            aio_pika.Message(
                body=json.dumps(block).encode()
            ),
            routing_key=e('RMQ_BLOCKS_QUEUE', 'blocks')
        )

        for transaction_hash in block.get('transactions', []):
            queue.put_nowait(transaction_hash)


async def parse_transaction(channel, session, transaction_hash):
    data = await fetch(session, 'eth_getTransactionByHash', [transaction_hash])
    if data:
        input_data = decode_contract_data(data.get('input'))
        data['input'] = input_data if input_data else None
        await channel.default_exchange.publish(
            aio_pika.Message(
                body=json.dumps(data).encode()
            ),
            routing_key=e('RMQ_TRANSACTIONS_QUEUE', 'transactions')
        )


async def main(loop, queue):
    connection = await aio_pika.connect_robust(
        f"amqp://{e('RMQ_USER', 'rabbitmq')}:{e('RMQ_PASSWORD', 'rabbitmq')}@{e('RMQ_HOST', 'localhost')}/",
        loop=loop
    )

    channel = await connection.channel()
    async with aiohttp.ClientSession(json_serialize=ujson.dumps) as session:
        while 1:
            try:
                transaction_hash = queue.get_nowait()
            except asyncio.QueueEmpty:
                try:
                    number = next(generator)
                    await parse_block(channel, session, queue, number)

                except StopIteration:
                    break
            else:
                await parse_transaction(channel, session, transaction_hash)

        await connection.close()


async def speedtest(queue):
    _hi = 0
    while True:
        _tmp = _LEN
        await asyncio.sleep(1)
        _speed = _LEN - _tmp
        if _hi < _speed:
            _hi = _speed

        sys.stdout.write(f"\rQUEUE LENGTH: {queue.qsize():05d} / HIGHEST SPEED: {_hi:05d} / CURRENT SPEED: {_speed:05d} RPS")
        sys.stdout.flush()


def run():
    queue = asyncio.Queue()
    workers_len = int(e('WORKERS', 80))
    print(f'WORKERS: {workers_len}')

    ioloop = asyncio.get_event_loop()

    workers = []
    for name in range(workers_len):
        workers.append(ioloop.create_task(main(ioloop, queue)))

    if e('SPEED_TEST', False):
        workers.append(ioloop.create_task(speedtest(queue)))
    wait_tasks = asyncio.wait(workers)

    ioloop.run_until_complete(wait_tasks)
    ioloop.close()


if __name__ == '__main__':
    run()
    print(f'DURATION: {start-time.time()}')
