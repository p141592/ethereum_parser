import json

from web3.auto.infura import w3
from web3.exceptions import BadFunctionCallOutput

from tools import toDict

ERC20_ABI = json.loads('[{"constant":true,"inputs":[],"name":"name","outputs":[{"name":"","type":"string"}],'
                       '"payable":false,"stateMutability":"view","type":"function"},{"constant":false,"inputs":[{'
                       '"name":"_spender","type":"address"},{"name":"_value","type":"uint256"}],"name":"approve",'
                       '"outputs":[{"name":"","type":"bool"}],"payable":false,"stateMutability":"nonpayable",'
                       '"type":"function"},{"constant":true,"inputs":[],"name":"totalSupply","outputs":[{"name":"",'
                       '"type":"uint256"}],"payable":false,"stateMutability":"view","type":"function"},'
                       '{"constant":false,"inputs":[{"name":"_from","type":"address"},{"name":"_to",'
                       '"type":"address"},{"name":"_value","type":"uint256"}],"name":"transferFrom","outputs":[{'
                       '"name":"","type":"bool"}],"payable":false,"stateMutability":"nonpayable","type":"function"},'
                       '{"constant":true,"inputs":[],"name":"decimals","outputs":[{"name":"","type":"uint8"}],'
                       '"payable":false,"stateMutability":"view","type":"function"},{"constant":true,"inputs":[{'
                       '"name":"_owner","type":"address"}],"name":"balanceOf","outputs":[{"name":"",'
                       '"type":"uint256"}],"payable":false,"stateMutability":"view","type":"function"},'
                       '{"constant":true,"inputs":[],"name":"symbol","outputs":[{"name":"","type":"string"}],'
                       '"payable":false,"stateMutability":"view","type":"function"},{"constant":false,"inputs":[{'
                       '"name":"_to","type":"address"},{"name":"_value","type":"uint256"}],"name":"transfer",'
                       '"outputs":[{"name":"","type":"bool"}],"payable":false,"stateMutability":"nonpayable",'
                       '"type":"function"},{"constant":true,"inputs":[{"name":"_owner","type":"address"},'
                       '{"name":"_spender","type":"address"}],"name":"allowance","outputs":[{"name":"",'
                       '"type":"uint256"}],"payable":false,"stateMutability":"view","type":"function"},'
                       '{"anonymous":false,"inputs":[{"indexed":true,"name":"_from","type":"address"},'
                       '{"indexed":true,"name":"_to","type":"address"},{"indexed":false,"name":"_value",'
                       '"type":"uint256"}],"name":"Transfer","type":"event"},{"anonymous":false,"inputs":[{'
                       '"indexed":true,"name":"_owner","type":"address"},{"indexed":true,"name":"_spender",'
                       '"type":"address"},{"indexed":false,"name":"_value","type":"uint256"}],"name":"Approval",'
                       '"type":"event"}]')

Contract = w3.eth.contract(abi=ERC20_ABI)


def enrichment_dec(func):
    def wrap(tx):
        _tx = dict(tx)
        _result, _erc20 = func(tx)
        if _result:
            _tx['input'] = _result
        return _tx, _erc20
    return wrap


@enrichment_dec
def enrichment_transaction(transaction):
    try:
        contract = get_erc20_contract(transaction.to)
        input_data = parse_input_data(contract, transaction)
    except ValueError:
        return None, None
    except TypeError:
        return None, None

    else:
        return input_data, parse_erc20(contract, transaction.to)


def parse_input_data(contract, transaction):
    _data = contract.decode_function_input(transaction.input)
    return dict(
        function=_data[0].fn_name,
        data=_data[1]
    )


def get_erc20_contract(address):
    return Contract(address=address)


def parse_erc20(erc20, address):
    try:
        name = erc20.functions.name().call()
        symbol = erc20.functions.symbol().call()
        decimals = erc20.functions.decimals().call()
        totalSupply = erc20.functions.totalSupply().call()

    except BadFunctionCallOutput:
        return None
    except OverflowError:
        return None

    return dict(
        name=name,
        address=address,
        symbol=symbol,
        decimals=decimals,
        totalSupply=totalSupply
    )
