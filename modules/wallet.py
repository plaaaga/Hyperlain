from eth_account.messages import (
    encode_defunct,
    encode_typed_data,
    _hash_eip191_message
)
from web3.middleware import geth_poa_middleware
from web3 import Web3

from modules.database import DataBase
import settings


class Wallet:
    def __init__(
            self,
            privatekey: str,
            encoded_pk: str,
            db: DataBase,
            browser=None,
            recipient: str = None,
    ):
        self.privatekey = privatekey
        self.encoded_pk = encoded_pk

        self.account = Web3().eth.account.from_key(privatekey)
        self.address = self.account.address
        self.recipient = Web3().to_checksum_address(recipient) if recipient else None
        self.browser = browser
        self.db = db


    def get_web3(self, chain_name: str):
        web3 = Web3(Web3.HTTPProvider(settings.RPCS[chain_name]))
        web3.middleware_onion.inject(geth_poa_middleware, layer=0)
        return web3


    def sign_message(
            self,
            text: str = None,
            typed_data: dict = None,
            hash: bool = False
    ):
        if text:
            message = encode_defunct(text=text)
        elif typed_data:
            message = encode_typed_data(full_message=typed_data)
            if hash:
                message = encode_defunct(hexstr=_hash_eip191_message(message).hex())

        signed_message = self.account.sign_message(message)
        signature = signed_message.signature.hex()
        if not signature.startswith('0x'): signature = '0x' + signature
        return signature

