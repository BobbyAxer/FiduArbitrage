import asyncio
from bxcommon.rpc.provider.ws_provider import WsProvider
from bxcommon.rpc.rpc_request_type import RpcRequestType
from bxcommon.rpc.json_rpc_request import JsonRpcRequest
from web3 import Web3
import os
import json
import base64
import getpass
from cryptography.fernet import Fernet
from dotenv import load_dotenv
from abi import abi_gfi, abi_curve
from addresses import gfi, curve, address_curve
import time
import requests
my_provider = Web3.IPCProvider('~/.ethereum/geth.ipc')
web3 = Web3(my_provider)
my_address = ''
contract = web3.eth.contract(address=gfi, abi=abi_gfi)
contract_curve = web3.eth.contract(address=Web3.toChecksumAddress(curve), abi=abi_curve)
ws_uri = "ws://127.0.0.1:28333"
auth_header = ""
load_dotenv()
#
decryptionkey = getpass.getpass()
def decrypt(token: bytes, key: bytes) -> bytes:
    return Fernet(key).decrypt(token)
private_key = decrypt(base64.b64decode(b'=='), decryptionkey).decode()
#nonce = web3.eth.getTransactionCount(my_address)
#print(nonce)
def telegram_bot_sendtext(bot_message):
    bot_token = ''
    bot_chatID = ''
    send_text = 'https://api.telegram.org/bot' + bot_token + '/sendMessage?chat_id=' + bot_chatID + '&parse_mode=Markdown&text=' + bot_message
    response = requests.get(send_text)
    return response.json()
async def test():
	while True:
		try:
			async with WsProvider(uri=ws_uri, headers={"Authorization": auth_header}) as ws:
				subscription_id = await ws.subscribe("newTxs", {"include": ["tx_contents"],"filters": "{method_id} == '0xc4076876' AND ({to} == '0x33fCf9230AD1d2950EE562fF0888b7240C7aa8eA')"})
				while True:
					next_notification = await ws.get_next_subscription_notification_by_id(subscription_id)
					tx = next_notification.notification['txContents']
					redeem_data = '0xdb006a75000000000000000000000000000000000000000000000000000000000000005c'
					withdraw_data = "0x58031d120000000000000000000000000000000000000000000009414e980bb006a80000"
					nonce = web3.eth.getTransactionCount(my_address)
					if tx['type'] == '0x2' and int(tx['maxFeePerGas'], 16) > 3000000000:
						print('executing trans...')
						transaction_withdraw = {
							'chainId': 1,
							'from': my_address,
							'to': gfi,
							'value': 0,
							# 'type': 2,
							'gas': 500000,
							'maxFeePerGas': int(tx['maxFeePerGas'], 16),
							'data': withdraw_data,
							'maxPriorityFeePerGas': int(tx['maxPriorityFeePerGas'], 16),
							'nonce': nonce + 1
						}
						transaction_redeem = {
							'chainId': 1,
							'from': my_address,
							'to': gfi,
							'value': 0,
							# 'type': 2,
							'gas': 500000,
							'maxFeePerGas': int(tx['maxFeePerGas'], 16),
							'data': redeem_data,
							'maxPriorityFeePerGas': int(tx['maxPriorityFeePerGas'], 16),
							'nonce': nonce
						}
						signed_redeem = web3.eth.account.sign_transaction(transaction_redeem, private_key=private_key)
						signed_withdraw = web3.eth.account.sign_transaction(transaction_withdraw, private_key=private_key)
						raw_redeem = signed_redeem.rawTransaction.hex()[2:]
						raw_withdraw = signed_withdraw.rawTransaction.hex()[2:]
						response = await ws.call(JsonRpcRequest(request_id="1", method="blxr_batch_tx",params={"transactions": [raw_redeem, raw_withdraw]}))
						#responce2 = await ws.call_bx(RpcRequestType.BLXR_TX, {"transaction": raw_withdraw})
						print(response)
						#print(responce2)
					elif tx['type'] == '0x0' and int(tx['gasPrice'], 16) > 3000000000:
						transaction_withdraw = {
							'chainId': 1,
							'from': my_address,
							"to": gfi,
							'value': 0,
							"gasPrice": int(tx['gasPrice'], 16),
							"gas": 500000,
							'data': withdraw_data,
							"nonce": nonce + 1
						}
						transaction_redeem = {
							'chainId': 1,
							'from': my_address,
							"to": gfi,
							'value': 0,
							"gasPrice": int(tx['gasPrice'], 16),
							"gas": 500000,
							'data': redeem_data,
							"nonce": nonce
						}
						signed_redeem = web3.eth.account.sign_transaction(transaction_redeem, private_key=private_key)
						signed_withdraw = web3.eth.account.sign_transaction(transaction_withdraw, private_key=private_key)
						raw_redeem = signed_redeem.rawTransaction.hex()[2:]
						raw_withdraw = signed_withdraw.rawTransaction.hex()[2:]
						response = await ws.call(JsonRpcRequest(request_id="1", method="blxr_batch_tx", params={"transactions": [raw_redeem, raw_withdraw]}))
						#responce2 = await ws.call_bx(RpcRequestType.BLXR_TX, {"transaction": raw_withdraw})
						print(response)
						#print(responce2)
		except Exception as e:
			print(f"Connection broken to feed, {str(e)}, retrying.")


def main():
    loop = asyncio.get_event_loop()
    loop.run_until_complete(test())
    loop.close()

if __name__ == '__main__':
    main()
