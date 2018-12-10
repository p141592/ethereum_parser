import asyncio


async def speedtest(loop, _len):
    while True:
        _tmp = _len
        await asyncio.sleep(1)
        print(_len - _tmp)
