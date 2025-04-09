from loguru import logger
from random import choice

from .wallet import Wallet
from .retry import retry
from .config import IDS_CHAIN
from .browser import CaptchaSolver
from settings import REGISTER_PARAMS


class Hyperlane(Wallet):
    typed_data: dict = {
        "domain": {"name": "Hyperlane", "version": "1"},
        "primaryType": "Message",
        "types": {
            "EIP712Domain": [{"name": "name", "type": "string"}, {"name": "version", "type": "string"}],
            "Message": [{"name": "eligibleAddress", "type": "string"}, {"name": "chainId", "type": "uint256"},
                        {"name": "amount", "type": "string"}, {"name": "receivingAddress", "type": "string"},
                        {"name": "tokenType", "type": "string"}]
        }
    }

    def __init__(self, wallet: Wallet):
        super().__init__(
            privatekey=wallet.privatekey,
            encoded_pk=wallet.encoded_pk,
            db=wallet.db,
            browser=wallet.browser,
            recipient=wallet.recipient
        )

        self.token = choice(REGISTER_PARAMS["tokens"])
        if self.token == "stHYPER":
            if "ethereum" not in REGISTER_PARAMS["chains"]:
                raise Exception(f'"stHYPER" can be claimed only in Ethereum')
            else:
                self.chain_name = "ethereum"
        else:
            self.chain_name = choice(REGISTER_PARAMS["chains"])
        self.web3 = self.get_web3(self.chain_name)
        self.chain_id = self.web3.eth.chain_id

        self.solve_captcha()


    @retry(source="Hyperlane", module_str="Registration", exceptions=Exception)
    def run(self):
        is_eligible = self.browser.is_address_eligible()
        if not is_eligible["eligible"]:
            logger.error(f'[-] Hyperlane | Wallet is not eligible')
            self.db.append_report(
                privatekey=self.encoded_pk,
                text="not eligible",
                success=False,
            )
            return True
        else:
            logger.info(f'[+] Hyperlane | Wallet eligible for {is_eligible["amount"]} HYPER')
            self.db.append_report(
                privatekey=self.encoded_pk,
                text=f'eligible for {is_eligible["amount"]} HYPER',
                success=True,
            )

        registration = self.browser.get_registration()
        if registration:
            registered_token = registration[0]["tokenType"]
            registered_chain = IDS_CHAIN[registration[0]["chainId"]]
            logger.success(f'[+] Hyperlane | Wallet already registered {registered_token} in {registered_chain.title()}')
            self.db.append_report(
                privatekey=self.encoded_pk,
                text=f'wallet already registered {registered_token} in {registered_chain}',
                success=True,
            )
            return True

        self.typed_data["message"] = {
            "eligibleAddress": self.address,
            "chainId": self.chain_id,
            "amount": is_eligible["amount"],
            "receivingAddress": self.address,
            "tokenType": self.token
        }
        signature = self.sign_message(typed_data=self.typed_data)
        self.browser.save_registration(
            chain_id=self.chain_id,
            signature=signature,
            token=self.token,
            amount=is_eligible["amount"]
        )
        logger.success(f'[+] Hyperlane | Registered {is_eligible["amount"]} {self.token} in {self.chain_name.title()}')
        self.db.append_report(
            privatekey=self.encoded_pk,
            text=f'registered {is_eligible["amount"]} {self.token} in {self.chain_name}',
            success=True,
        )

        return True


    def solve_captcha(self):
        resp = self.browser.get_vercel_captcha()
        if "X-Vercel-Challenge-Token" not in resp.headers:
            return

        captcha_solution = CaptchaSolver().solve(token=resp.headers["X-Vercel-Challenge-Token"])
        self.browser.post_vercel_captcha(token=resp.headers["X-Vercel-Challenge-Token"], solution=captcha_solution)
