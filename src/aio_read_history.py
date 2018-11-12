import time
import ujson
import requests
import aiohttp
import asyncio

from rmq import RMQ

start = time.time()

blocks_queue = asyncio.Queue()
transactions_queue = asyncio.Queue()

DATA_MAP = dict(
    difficulty=lambda x: int(x, 16),
)


def prepare_data(func):
    async def wrap(*args):
        data = await func(*args)
        if data:
            result = dict()
            for k, v in ujson.loads(data).get('result').items():
                if DATA_MAP.get(k):
                    result[k] = DATA_MAP[k](v)
                    continue

                result[k] = v
            return result

    return wrap


def get_blocks_count():
    r = requests.get('https://api.infura.io/v1/jsonrpc/mainnet/eth_blockNumber')
    return int(r.json().get('result'), 16)


def send_data(data, routing_key):
    with RMQ() as rmq:
        rmq.send_data(data, routing_key)


async def block_worker(queue):
    while True:
        params = await queue.get()
        async with aiohttp.ClientSession() as session:
            block = await fetch(session, 'eth_getBlockByNumber', params)
            if block:
                send_data(block, 'blocks')

                for transaction_hash in block.get('transactions', []):
                    transactions_queue.put_nowait(transaction_hash)

        queue.task_done()


async def transaction_worker(queue):
    while True:
        transaction_hash = await queue.get()
        async with aiohttp.ClientSession() as session:
            data = await fetch(session, 'eth_getTransactionByHash', [transaction_hash])
            if data:
                send_data(data, 'transaction')

        queue.task_done()


@prepare_data
async def fetch(session, method, params):
    data = {"jsonrpc": "2.0", "method": method, "params": params, "id": 1}
    try:
        async with session.post(
                'https://mainnet.infura.io/',
                json=data,
                headers={'Content-Type': 'application/json'},
                timeout=aiohttp.ClientTimeout(total=5)
        ) as response:
            return await response.text()

    except Exception as e:
        print(e)
        send_data(dict(
            request=data,
            exception=e
        ), 'errors')


async def main(_from=6008149, _to=get_blocks_count()):

    for block_number in range(_from, _to):
        blocks_queue.put_nowait([hex(block_number), False])

    for i in range(3):
        asyncio.create_task(block_worker(blocks_queue))
        asyncio.create_task(transaction_worker(transactions_queue))

    await blocks_queue.join()
    await transactions_queue.join()


def run(**kwargs):
    asyncio.run(main(**kwargs))


if __name__ == '__main__':
    run()
    print(f'DURATION: {start-time.time()}')
