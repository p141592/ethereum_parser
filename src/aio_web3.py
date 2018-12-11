import asyncio
import os
import sys
import time
import rapidjson as json
import aio_pika
from web3.auto.infura import w3

from data import get_blocks_count
from erc20 import enrichment_transaction
from tools import toDict

start = time.time()
e = os.environ.get

_LEN = 0


def block_number_generator(_from, _to):
    for number in range(int(_from), int(_to)) if not e('BLOCKS') else json.loads(e('BLOCKS')):
        yield number


generator = block_number_generator(int(e('RANGE_FROM', 0)), int(e('RANGE_TO', get_blocks_count())))


async def main(loop):
    connection = await aio_pika.connect_robust(
        f"amqp://{e('RMQ_USER', 'rabbitmq')}:{e('RMQ_PASSWORD', 'rabbitmq')}@{e('RMQ_HOST', 'localhost')}/",
        loop=loop
    )

    channel = await connection.channel()
    while True:
        try:
            number = next(generator)
            block = w3.eth.getBlock(number, full_transactions=True)

            for tx in block.transactions:
                tx = enrichment_transaction(tx)
                tx.update(w3.eth.getTransactionReceipt(tx['hash']))
                if e('DEBUG', False):
                    print('=' * 150)
                    print(tx)
            #print(f'{number}: DONE')

            await channel.default_exchange.publish(
                aio_pika.Message(
                    body=json.dumps(toDict(block)).encode()
                ),
                routing_key=e('RMQ_TRANSACTIONS_QUEUE', 'transactions')
            )
        except StopIteration:
            break

    connection.close()


async def speedtest():
    _hi = 0
    while True:
        _tmp = _LEN
        await asyncio.sleep(1)
        _speed = _LEN - _tmp
        if _hi < _speed:
            _hi = _speed

        sys.stdout.write(f"\rHIGHEST SPEED: {_hi:05d} / CURRENT SPEED: {_speed:05d} RPS")
        sys.stdout.flush()


def run():
    workers_len = int(e('WORKERS', 80))
    print(f'WORKERS: {workers_len}')

    ioloop = asyncio.get_event_loop()

    workers = []
    for name in range(workers_len):
        workers.append(ioloop.create_task(main(ioloop)))

    if e('SPEED_TEST', False):
        workers.append(ioloop.create_task(speedtest()))
    wait_tasks = asyncio.wait(workers)

    ioloop.run_until_complete(wait_tasks)
    ioloop.close()


if __name__ == '__main__':
    run()
    print(f'DURATION: {start-time.time()}')
