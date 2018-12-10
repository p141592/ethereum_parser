TMP_METHODS = set()


def empty(data):
    return None


def unknown(data):
    return data


def transfer(data): # Transfer given number of tokens from message sender to given recipient
    pass


def get_method(data):
    _method = data[:10]
    return _method if _method in METHODS_MAP else 'unknown'


METHODS_MAP = {
    'unknown': unknown,
    '0x': empty,
    '0xa9059cbb': transfer,  # allowance
    #'0x9e281a98': withdrawToken,  # approve
    # '0xa9059cbb': '',  # transferFrom
    # '0xa9059cbb': '',  # transfer
    # '0xa9059cbb': '',  # balanceOf
    # '0xa9059cbb': '',  # totalSupply
    # '0xa9059cbb': '',  # decimals
    # '0xa9059cbb': '',  # symbol
    # '0xa9059cbb': ''  # name
}


def decode_contract_data(raw_input):
    _method = get_method(raw_input)
    _data = METHODS_MAP.get(_method)(raw_input)
    if _data:
        return dict(
            method=_method,
            data=_data
        )
