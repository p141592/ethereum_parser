import gevent
import os
import sys
import time
import rapidjson as json
import pika

from pika.exceptions import ConnectionClosed
from data import get_blocks_count
from erc20 import enrichment_transaction, ERC20
from tools import toDict

start = time.time()
e = os.environ.get

if e('IPC_PATH'):
    from web3 import Web3
    w3 = Web3(Web3.IPCProvider(e('IPC_PATH')))
else:
    from web3.auto.infura import w3


def block_number_generator(_from, _to):
    for number in range(int(_from), int(_to)) if not e('BLOCKS') else json.loads(e('BLOCKS')):
        yield number


generator = block_number_generator(int(e('RANGE_FROM', 0)), int(e('RANGE_TO', get_blocks_count())))


def main(channel):
        try:
            number = next(generator)
            block = w3.eth.getBlock(number, full_transactions=True)

            for tx in block.transactions:
                tx, erc20 = enrichment_transaction(tx)
                tx.update(w3.eth.getTransactionReceipt(tx['hash']))
                if e('DEBUG', False):
                    print('='*150)
                    print(tx)

                if erc20 and erc20.get('address') not in ERC20:
                    channel.basic_publish(
                        exchange=e('RMQ_EXCHANGE', 'ethereum'),
                        routing_key=e('RMQ_ERC20_QUEUE', 'erc20'),
                        body=json.dumps(toDict(erc20)).encode()
                    )
                    ERC20.add(erc20.get('address'))

                    if e('DEBUG', False):
                        print('== NEW ERC20')

            print(f'{number}: DONE')

            channel.basic_publish(
                exchange=e('RMQ_EXCHANGE', 'ethereum'),
                routing_key=e('RMQ_BLOCKS_QUEUE', 'blocks'),
                body=json.dumps(toDict(block)).encode()
            )

        except StopIteration:
            return




# async def speedtest():
#     _hi = 0
#     global _LEN
#     while True:
#         _tmp = _LEN
#         await asyncio.sleep(1)
#         _speed = _LEN - _tmp
#         if _hi < _speed:
#             _hi = _speed
#
#         sys.stdout.write(f"\rPARSED: {_LEN} / HIGHEST SPEED: {_hi:05d} / CURRENT SPEED: {_speed:05d} (Transactions per Second)")
#         sys.stdout.flush()
#
#
# async def healthcheck():
#     _tmp = _LEN
#     while True:
#         await asyncio.sleep(10)
#         if _LEN == _tmp:
#             sys.stdout.write(f"\n== Work is finished\n")
#             sys.exit(1)
#         _tmp = _LEN
#
#
# def run():
#     workers_len = int(e('WORKERS', 80))
#     print(f'WORKERS: {workers_len}')
#
#     ioloop = asyncio.get_event_loop()
#
#     # workers = []
#     # if e('SPEED_TEST', False):
#     #     workers.append(ioloop.create_task(speedtest()))
#
#     for name in range(workers_len):
#         workers.append(ioloop.create_task(main(ioloop)))
#
#     # workers.append(ioloop.create_task(healthcheck()))
#
#     wait_tasks = asyncio.wait(workers)
#     ioloop.run_until_complete(wait_tasks)
#     ioloop.close()


def run():
    #main()
    try:
        credentials = pika.PlainCredentials(e('RMQ_USER', 'rabbitmq'), e('RMQ_PASSWORD', 'rabbitmq'))
        parameters = pika.ConnectionParameters(e('RMQ_HOST', 'localhost'),
                                               int(e('RMQ_PORT', 5672)),
                                               e('RMQ_VHOST', '/'),
                                               credentials)
        rmq_conn = pika.BlockingConnection(parameters=parameters)
        channel = rmq_conn.channel()

    except ConnectionClosed:
        print('=' * 50)
        print('!!! RMQ problems !!!')
        print('=' * 50)
        sys.exit(0)

    threads = []
    for i in range(int(e('WORKERS', 10))):
        threads.append(gevent.spawn(main, channel))
    gevent.joinall(threads)

    rmq_conn.close()


if __name__ == '__main__':
    run()
    print(f'DURATION: {start-time.time()}')
