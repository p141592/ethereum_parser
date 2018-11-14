import os
import aiohttp
import asyncio
import time

from data import prepare_data, get_blocks_count
from rmq import send_data

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
async def fetch(data):
    #try:
    async with aiohttp.ClientSession() as session:
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
    ## Если есть request_data -- Продолжить со старыми данными
    ## Если warning_length > _warning -- Закрыть worker
    ## Если в queue есть задача -- Получить задачу
    ## Если нет -- Получить новый номер блока
    ## Если номеров не осталось -- закруть worker

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

            print(f'REQUEST_DATA: {request_data}')

            data = await fetch({
                "jsonrpc": "2.0",
                "method": request_data.get('method'),
                "params": request_data.get('params'),
                "id": 1
            })
            print(f'DATA: {data}')
            if data:
                _warnings = 0
                send_data(data, request_data.get('method'))

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
            print('Слишком большое количество ошибок')

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
    asyncio.run(main())
    print(f'DURATION: {start-time.time()}')


if __name__ == '__main__':
    run()
