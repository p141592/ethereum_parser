import aiohttp
import asyncio
import time

from data import prepare_data
from rmq import send_data

start = time.time()


async def put_task(queue, data):
    await queue.put(data)


@prepare_data
async def fetch(data):
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                    'https://mainnet.infura.io/v3/c5008af68e8f4de9a59f16f58a51b967',
                    json=data,
                    headers={'Content-Type': 'application/json'},
                    timeout=aiohttp.ClientTimeout(total=5)
            ) as response:
                return await response.text()
    except :
        return


async def worker(queue):
    request_data = None
    warning_length = 50
    _warnings = 0
    while warning_length > _warnings:
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
                    queue.put_nowait(dict(
                        method='eth_getTransactionByHash',
                        params=[transaction_hash]
                    ))

                print(f'{int(time.time())}:  TASK DONE {queue.qsize()}')
                request_data = None
                queue.task_done()

        except asyncio.CancelledError:
            print(f'{int(time.time())}: TASK Cancelled {queue.qsize()} ')
            continue

        except asyncio.TimeoutError:
            print(f'{int(time.time())}: TASK Timeout {queue.qsize()} ')
            continue

        _warnings += 1

    else:
        print('='*25)
        print('Слишком большое количество ошибок\n  Поток закрыт')


async def main(_from=0, _to=2):
    print('GENERATING QUEUE ...')
    r_queue = asyncio.LifoQueue()
    for number in range(_from, _to):
        await put_task(r_queue, dict(
            method='eth_getBlockByNumber',
            params=[hex(number), False]
        ))
    print('DONE')
    print(f'= Queue size: {r_queue.qsize()}')
    time.sleep(2)
    print('GENERATING WORKERS ...')
    workers = []
    for _ in range(70):
        workers.append(asyncio.create_task(worker(r_queue)))
    print('DONE')
    print(f'= Workers length: {len(workers)}')

print('START')
print(f'= time: {start}')
asyncio.run(main())
print(f'DURATION: {start-time.time()}')
