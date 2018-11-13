import asyncio
import time
import aiohttp

from data import fetch, get_blocks_count
from rmq import send_data

start = time.time()


async def main(_from=0, _to=get_blocks_count()):
    async with aiohttp.ClientSession() as session:
        for number in range(_from, _to):
            block = await fetch(session, 'eth_getBlockByNumber', [hex(number), False])
            print(block)
            if block:
                send_data(block, 'eth_getBlockByNumber')

                for transaction_hash in block.get('transactions', []):
                    print(transaction_hash)
                    data = await fetch(session, 'eth_getTransactionByHash', [transaction_hash])
                    if data:
                        send_data(data, 'eth_getTransactionByHash')


def run(**kwargs):
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main(**kwargs))
    loop.close()


if __name__ == '__main__':
    run()
    print(f'DURATION: {start-time.time()}')
