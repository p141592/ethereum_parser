import os
import time

e = os.environ.get

if __name__ == '__main__':
    if e('TIME_SLEEP'):
        time.sleep(int(e('TIME_SLEEP')))
    from aio_web3 import run
    run()
