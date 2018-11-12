import asyncio
import time
import aiohttp

from data import prepare_data, get_blocks_count
from rmq import send_data

start = time.time()


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
        send_data(dict(
            request=data,
            exception=e
        ), 'errors')


async def main(_from=6008149, _to=get_blocks_count()):
    for number in range(_from, _to):
        async with aiohttp.ClientSession() as session:
            block = await fetch(session, 'eth_getBlockByNumber', [hex(number), False])
            if block:
                send_data(block, 'blocks')

                for transaction_hash in block.get('transactions', []):
                    data = await fetch(session, 'eth_getTransactionByHash', [transaction_hash])
                    if data:
                        send_data(data, 'transaction')


def run(**kwargs):
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main(**kwargs))
    loop.close()


if __name__ == '__main__':
    run()
    print(f'DURATION: {start-time.time()}')
