import time

import requests

from rmq import RMQ

start = time.time()


def get_blocks_count():
    r = requests.get('https://api.infura.io/v1/jsonrpc/mainnet/eth_blockNumber')
    return int(r.json().get('result'), 16)


def fetch(number):
    data = {"jsonrpc": "2.0", "method": "eth_getBlockByNumber", "params": [hex(number), False], "id": 1}
    r = requests.post('https://mainnet.infura.io/', json=data, headers={'Content-Type': 'application/json'})
    return dict(
        result=True,
        data=r.text
    )


for i in range(1, 10):
    with RMQ() as rmq:
        rmq.send_data(fetch(i))

print(f'DURATION: {start-time.time()}')
