import asyncio
import os
import time
import ujson
import rapidjson as json
import aiohttp
import aioredis as aioredis

from data import get_blocks_count, prepare_data

start = time.time()
e = os.environ.get


def block_number_generator(_from, _to):
    for number in range(int(_from), int(_to)) if not e('BLOCKS') else json.loads(e('BLOCKS')):
        yield number


generator = block_number_generator(int(e('RANGE_FROM', 0)), int(e('RANGE_TO', get_blocks_count())))


@prepare_data
async def fetch(session, method, params):
    data = {"jsonrpc": "2.0", "method": method, "params": params, "id": 1}
    async with session.post(
            'https://mainnet.infura.io/v3/c5008af68e8f4de9a59f16f58a51b967',
            json=data,
            headers={'Content-Type': 'application/json'},
            timeout=aiohttp.ClientTimeout(total=e('HTTP_TIMEOUT', 5))
    ) as response:
        return await response.text()


async def main(loop, _from=0, _to=get_blocks_count()):

    connection = await aioredis.create_redis(f"redis://{e('REDIS_HOST', 'localhost')}/{e('REDIS_DB', 1)}", loop=loop)
    async with aiohttp.ClientSession(json_serialize=ujson.dumps) as session:
        while 1:
            try:
                number = next(generator)
                block = await fetch(session, 'eth_getBlockByNumber', [hex(number), False])

                if block:
                    await connection.execute(
                        'lpush',
                        e('RMQ_BLOCKS_QUEUE', 'blocks'),
                        json.dumps(block).encode()
                    )

                    for transaction_hash in block.get('transactions', []):
                        data = await fetch(session, 'eth_getTransactionByHash', [transaction_hash])
                        if data:
                            await connection.execute(
                                'lpush',
                                e('RMQ_TRANSACTIONS_QUEUE', 'transactions'),
                                json.dumps(data).encode()
                            )

            except StopIteration:
                break

            print(f'{number}: DONE')

        connection.close()


def run():
    workers_len = int(e('WORKERS', 80))

    ioloop = asyncio.get_event_loop()

    workers = []
    for name in range(workers_len):
        workers.append(ioloop.create_task(main(ioloop)))

    wait_tasks = asyncio.wait(workers)

    ioloop.run_until_complete(wait_tasks)
    ioloop.close()


if __name__ == '__main__':
    run()
    print(f'DURATION: {start-time.time()}')
