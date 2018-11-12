import aiohttp
import ujson

import requests

from rmq import send_data

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


@prepare_data
async def fetch(session, method, params):
    data = {"jsonrpc": "2.0", "method": method, "params": params, "id": 1}
    try:
        async with session.post(
                'https://mainnet.infura.io/',
                json=data,
                headers={'Content-Type': 'application/json'},
                timeout=aiohttp.ClientTimeout(total=15)
        ) as response:
            return await response.text()

    except Exception as e:
        send_data(dict(
            request=data,
            exception=e
        ), 'errors')
