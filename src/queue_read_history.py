import os

import aiohttp
import asyncio
import time

from data import prepare_data, get_blocks_count
from rmq import send_data

e = os.environ.get

start = time.time()


async def put_task(queue, data):
    await queue.put(data)


@prepare_data
async def fetch(data):
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                    e.get('NODE_URL'),
                    json=data,
                    headers={'Content-Type': 'application/json'},
                    timeout=aiohttp.ClientTimeout(total=int(e('HTTP_TIMEOUT', 5)))
            ) as response:
                return await response.text()
    except :
        return


async def worker(queue):
    request_data = None
    warning_length = 50
    _warnings = 0
    while (warning_length > _warnings or queue.qsize() != 0) and not request_data:
        try:
            if request_data:
                print(f'{int(time.time())}: RE-CREATED TASK {queue.qsize()}')

            request_data = await queue.get() if not request_data else request_data

            data = await fetch({
                "jsonrpc": "2.0",
                "method": request_data.get('method'),
                "params": request_data.get('params'),
                "id": 1
            })

            if data:
                _warnings = 0
                send_data(data, request_data.get('method'))

                for transaction_hash in data.get('transactions', []):
                    # print(transaction_hash)
                    await put_task(queue, dict(
                        method='eth_getTransactionByHash',
                        params=[transaction_hash]
                    ))

                print(f'{int(time.time())}:  TASK DONE {queue.qsize()}')
                request_data = None
                queue.task_done()
                if queue.qsize() == 0:
                    break
            #print(request_data)

        except asyncio.CancelledError:
            print(f'{int(time.time())}: TASK Cancelled {queue.qsize()} ')
            continue

        except asyncio.TimeoutError:
            print(f'{int(time.time())}: TASK Timeout {queue.qsize()} ')
            continue

        _warnings += 1
        #await asyncio.sleep(1)

    else:
        if warning_length == _warnings:
            print('='*25)
            print('Слишком большое количество ошибок')
        print('Worker закрыт')


async def main():
    print('GENERATING QUEUE ...')
    r_queue = asyncio.LifoQueue()
    for number in range(
            int(e('RANGE_FROM', 0)),
            int(e('RANGE_TO', get_blocks_count()))
    ):
        await put_task(r_queue, dict(
            method='eth_getBlockByNumber',
            params=[hex(number), False]
        ))

    print('DONE')
    print(f'= Queue size: {r_queue.qsize()}')

    print('GENERATING WORKERS ...')
    workers = []
    for _ in range(int(e('WORKERS', 30))):
        workers.append(asyncio.create_task(worker(r_queue)))
    print('DONE')
    print(f'= Workers length: {len(workers)}')


def run():
    print('START')
    print(f'= time: {start}')
    asyncio.run(main())
    print(f'DURATION: {start-time.time()}')


if __name__ == '__main__':
    run()
