import os
import sys

import aiohttp
import asyncio
import time

import pika as pika
from pika.exceptions import ConnectionClosed

from data import prepare_data, get_blocks_count

e = os.environ.get

BLOCKS = None

start = time.time()


async def put_task(queue, data):
    await queue.put(data)


def block_number_generator():
    for number in range(
            int(e('RANGE_FROM', 0)),
            int(e('RANGE_TO', get_blocks_count()))
    ):
        yield number


@prepare_data
async def fetch(session, data):
    #try:
    async with session.post(
            e('NODE_URL', 'https://mainnet.infura.io/v3/c5008af68e8f4de9a59f16f58a51b967'),
            json=data,
            headers={'Content-Type': 'application/json'},
            timeout=aiohttp.ClientTimeout(total=int(e('HTTP_TIMEOUT', 5)))
    ) as response:
        return await response.text()
    #except:
    #    return


async def worker(name, queue):
    request_data = None
    warning_length = 50
    _warnings = 0
    global BLOCKS

    try:
        credentials = pika.PlainCredentials(e('RMQ_USER', 'rabbitmq'), e('RMQ_PASSWORD', 'rabbitmq'))
        parameters = pika.ConnectionParameters(e('RMQ_HOST', 'localhost'),
                                               int(e('RMQ_PORT', 5672)),
                                               e('RMQ_VHOST', '/'),
                                               credentials)

        rmq_conn = pika.BlockingConnection(parameters=parameters)

    except ConnectionClosed:
        print('=' * 50)
        print('!!! RMQ problems !!!')
        print('=' * 50)
        sys.exit(0)

    else:
        async with aiohttp.ClientSession() as session:
            while warning_length > _warnings:
                try:
                    # Получение задачи
                    if request_data:
                        print(f'{int(time.time())}: RE-CREATED TASK {queue.qsize()}')

                    else:
                        if queue.qsize() > 0:
                            request_data = await queue.get()

                        else:
                            request_data = dict(
                                method='eth_getBlockByNumber',
                                params=[hex(next(BLOCKS)), False],
                                block_task=True
                            )

                    #print(f'REQUEST_DATA: {request_data}')

                    data = await fetch(session, {
                        "jsonrpc": "2.0",
                        "method": request_data.get('method'),
                        "params": request_data.get('params'),
                        "id": 1
                    })
                    #print(f'DATA: {data}')
                    if data:
                        _warnings = 0
                        channel = rmq_conn.channel()
                        channel.basic_publish(
                            exchange=e('RMQ_EXCHANGE', 'ethereum'),
                            routing_key=e('RMQ_BLOCKS_QUEUE', 'blocks') if request_data.get('block_task') else e('RMQ_TRANSACTIONS_QUEUE', 'transactions'),
                            body=str(data)
                        )

                        for transaction_hash in data.get('transactions', []):
                            # print(transaction_hash)
                            await put_task(queue, dict(
                                method='eth_getTransactionByHash',
                                params=[transaction_hash],
                                block_task=False
                            ))

                        print(f'{int(time.time())}: TASK DONE {queue.qsize()}')

                        if not request_data.get('block_task'):
                            queue.task_done()

                        request_data = None

                except asyncio.CancelledError:
                    print(f'{int(time.time())}: TASK Cancelled {queue.qsize()} ')
                    continue

                except asyncio.TimeoutError:
                    print(f'{int(time.time())}: TASK Timeout {queue.qsize()} ')
                    continue

                except StopIteration:
                    break

                _warnings += 1

            else:
                if warning_length == _warnings:
                    print('='*25)
                    #print('Слишком большое количество ошибок')

    rmq_conn.close()
    print('Worker закрыт')


async def main():
    print('GENERATING QUEUE ...')
    r_queue = asyncio.LifoQueue()
    global BLOCKS
    BLOCKS = block_number_generator()
    print('DONE')

    print('GENERATING WORKERS ...')
    workers = []
    for name in range(int(e('WORKERS', 40))):
        workers.append(asyncio.create_task(worker(name, r_queue)))
    print('DONE')
    print(f'= Workers length: {len(workers)}')


def run():
    print('START')
    print(f'= time: {start}')
    time.sleep(int(e('SLEEP', 0)))
    asyncio.run(main())
    print(f'DURATION: {start-time.time()}')


if __name__ == '__main__':
    run()
