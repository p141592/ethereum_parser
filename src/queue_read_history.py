import aiohttp
import asyncio
import time

from data import fetch, get_blocks_count
from rmq import send_data

start = time.time()


async def worker(queue):
        while True:
            request_data = await queue.get()
            #print(request_data)
            async with aiohttp.ClientSession() as session:
                block = await fetch(session, request_data.get('method'), request_data.get('params'))
                if block:
                    send_data(block, request_data.get('method'))

                    for transaction_hash in block.get('transactions', []):
                        print(transaction_hash)
                        queue.put_nowait(dict(
                            method='eth_getTransactionByHash',
                            params=[transaction_hash]
                        ))

            queue.task_done()


async def main(_from=6008149, _to=get_blocks_count()):
    r_queue = asyncio.Queue()
    for number in range(_from, _to):
        r_queue.put_nowait(dict(
            method='eth_getBlockByNumber',
            params=[hex(number), False]
        ))

    tasks = []
    for _ in range(80):
        task = asyncio.create_task(worker(r_queue))
        tasks.append(task)
    print(r_queue)


asyncio.run(main())
print(f'DURATION: {start-time.time()}')
