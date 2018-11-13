import aiohttp
import asyncio
import time

from data import get_blocks_count, prepare_data
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
                print(f'{queue.qsize()} RE-CREATED TASK')
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

                print(f'{queue.qsize()} TASK DONE')
                request_data = None
                queue.task_done()

        except asyncio.CancelledError:
            print(f'{queue.qsize()} TASK Cancelled')
            continue

        except asyncio.TimeoutError:
            print(f'{queue.qsize()} TASK Timeout')
            continue

        _warnings += 1

    else:
        print('='*25)
        print('Слишком большое количество ошибок\n  Поток закрыт')


async def main(_from=6008149, _to=get_blocks_count()):
    r_queue = asyncio.LifoQueue()
    for number in range(_from, _to):
        await put_task(r_queue, dict(
            method='eth_getBlockByNumber',
            params=[hex(number), False]
        ))

    for _ in range(100):
        asyncio.create_task(worker(r_queue))


asyncio.run(main())
print(f'DURATION: {start-time.time()}')
