import json

from web3.auto import w3

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


async def parse_transaction(transaction):
    # Получили транзакцию
    # transaction = w3.eth.getTransaction('0x7e84c4538e056f03ab689d1b0b112b47921b2f82fea0396bfa38194b6461ffdd')
    if not w3.toText(w3.toText(transaction.input)):
        # Проверить input_data
        return json.dumps(transaction, cls=toDict)
        # -> Вернуть результат

    # Если есть:
    # По адресу получателя получить контракт
    erc20 = await get_erc20_contract(transaction.to)
    # Проверить на erc20
    # Спарсить input_data

    return await parse_input_data(erc20, transaction.to)


async def parse_input_data(contract, transaction):
    return dict(
        function=contract.decode_function_input(transaction.input)[0].fn_name(),
        data=contract.decode_function_input(transaction.input)[1]
    )


async def get_erc20_contract(address):
    return await w3.eth.contract(address=address, abi=ERC20_ABI)


async def parse_erc20(address):
    erc20 = await get_erc20_contract(address)
    return dict(
        name=await erc20.functions.name().call(),
        symbol=await erc20.functions.symbol().call(),
        decimals=await erc20.functions.decimals().call(),
        totalSupply=await erc20.functions.totalSupply().call()
    )
