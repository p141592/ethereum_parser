import asyncio
import time
import aiohttp

from data import fetch
from rmq import send_data

start = time.time()


async def main(_from=6008149, _to=6008150):
    async with aiohttp.ClientSession() as session:
        for number in range(_from, _to):
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
