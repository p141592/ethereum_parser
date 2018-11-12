import argparse
import logging
import os

logging.basicConfig(format='%(asctime)-15s %(clientip)s %(user)-8s %(message)s')
e = os.environ.get

DEBUG = None
LOGGER = None


def main(kwargs):
    DEBUG = kwargs.get('debug')

    if DEBUG:
        print(kwargs)

    if kwargs.get('command') == 'get_history':
        from aio_read_history import run
        run(_from=1, _to=2)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Process some integers.')
    parser.add_argument('--debug', action='store_const', const=True)
    parser.add_argument('command')

    main(parser.parse_args().__dict__)
