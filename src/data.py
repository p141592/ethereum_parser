import ujson

import requests

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
