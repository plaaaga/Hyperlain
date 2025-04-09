from tls_client import Session
from requests import get
from time import sleep

from modules.retry import retry, have_json, CustomError
from modules.database import DataBase
from modules.utils import logger
import settings


class Browser:
    def __init__(self, db: DataBase, encoded_pk: str, proxy: str):
        self.max_retries = 5
        self.db = db
        self.encoded_pk = encoded_pk

        if proxy == "mobile":
            if settings.PROXY not in ['https://log:pass@ip:port', 'http://log:pass@ip:port', 'log:pass@ip:port', '', None]:
                self.proxy = settings.PROXY
            else:
                self.proxy = None
        else:
            if proxy not in ['https://log:pass@ip:port', 'http://log:pass@ip:port', 'log:pass@ip:port', '', None]:
                self.proxy = "http://" + proxy.removeprefix("https://").removeprefix("http://")
                logger.debug(f'[•] Soft | Got proxy {self.proxy}')
            else:
                self.proxy = None

        if self.proxy:
            if proxy == "mobile": self.change_ip()
        else:
            logger.warning(f'[-] Soft | You dont use proxies!')

        self.session = self.get_new_session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Safari/605.1.15",
        })
        self.address = None


    def get_new_session(self):
        session = Session(
            client_identifier="safari_16_0",
            random_tls_extension_order=True
        )

        if self.proxy:
            session.proxies.update({'http': self.proxy, 'https': self.proxy})

        return session


    @have_json
    def send_request(self, **kwargs):
        if kwargs.get("method"): kwargs["method"] = kwargs["method"].upper()
        return self.session.execute_request(**kwargs)


    def change_ip(self):
        if settings.CHANGE_IP_LINK not in ['https://changeip.mobileproxy.space/?proxy_key=...&format=json', '']:
            print('')
            while True:
                try:
                    r = get(settings.CHANGE_IP_LINK)
                    if 'mobileproxy' in settings.CHANGE_IP_LINK and r.json().get('status') == 'OK':
                        logger.debug(f'[+] Proxy | Successfully changed ip: {r.json()["new_ip"]}')
                        return True
                    elif not 'mobileproxy' in settings.CHANGE_IP_LINK and r.status_code == 200:
                        logger.debug(f'[+] Proxy | Successfully changed ip: {r.text}')
                        return True
                    logger.error(f'[-] Proxy | Change IP error: {r.text} | {r.status_code}')
                    sleep(10)

                except Exception as err:
                    logger.error(f'[-] Browser | Cannot get proxy: {err}')

    @retry(source="Browser", module_str="Get Vercel Captcha", exceptions=Exception)
    def get_vercel_captcha(self):
        return self.session.get(
            url='https://claim.hyperlane.foundation/',
            headers={
                "Origin": "https://claim.hyperlane.foundation",
                "Referer": "https://claim.hyperlane.foundation/"
            }
        )

    @retry(source="Browser", module_str="Post Vercel Captcha", exceptions=Exception)
    def post_vercel_captcha(self, token: str, solution: str):
        r = self.session.post(
            url='https://claim.hyperlane.foundation/.well-known/vercel/security/request-challenge',
            headers={
                "Origin": "https://claim.hyperlane.foundation",
                "Referer": "https://claim.hyperlane.foundation/",
                "X-Vercel-Challenge-Solution": solution,
                "X-Vercel-Challenge-Token": token,
                "X-Vercel-Challenge-Version": "2",
            }
        )
        if r.status_code != 204:
            raise CustomError(f'Failed to solve Vercel')


    @retry(source="Browser", module_str="Is address eligible", exceptions=Exception)
    def is_address_eligible(self):
        r = self.send_request(
            method="GET",
            url=f'https://claim.hyperlane.foundation/api/check-eligibility?address={self.address}',
            headers={
                "Origin": "https://claim.hyperlane.foundation",
                "Referer": "https://claim.hyperlane.foundation/"
            }
        )
        if r.json()["response"]["eligibilities"]:
            return {"eligible": True, "amount": r.json()["response"]["eligibilities"][0]["amount"]}
        else:
            return {"eligible": False, "amount": 0}

    @retry(source="Browser", module_str="Get registration", exceptions=Exception)
    def get_registration(self):
        r = self.send_request(
            method="GET",
            url=f'https://claim.hyperlane.foundation/api/get-registration-for-address?address={self.address}',
            headers={
                "Origin": "https://claim.hyperlane.foundation",
                "Referer": "https://claim.hyperlane.foundation/"
            }
        )
        return r.json().get("response")

    @retry(source="Browser", module_str="Get registration", exceptions=Exception)
    def save_registration(self, chain_id: int, signature: str, token: str, amount: str):
        r = self.send_request(
            method="POST",
            url='https://claim.hyperlane.foundation/api/save-registration',
            json={
                "wallets": [{
                    "eligibleAddress": self.address,
                    "chainId": chain_id,
                    "eligibleAddressType": "ethereum",
                    "receivingAddress": self.address,
                    "signature": signature,
                    "tokenType": token,
                    "amount": amount
                }]
            },
            headers={
                "Origin": "https://claim.hyperlane.foundation",
                "Referer": "https://claim.hyperlane.foundation/airdrop-registration"
            }
        )
        if r.json().get("validationResult") and r.json()["validationResult"].get("success") is True:
            return True
        else:
            raise Exception(f'Unexpected response: {r.json()["message"]}')


class CaptchaSolver:
    def __init__(self):
        self.api_link = "https://captcha.solvium.io/api/v1/task"

    def solve(self, token: str):
        task_id = self.request_solving(token=token)
        logger.debug(f'[•] Captcha | Waiting for solve captcha #{task_id}')
        return self.get_result(task_id)

    def request_solving(self, token: str):
        r = get(
            url=f"{self.api_link}/vercel",
            params={"challengeToken": token},
            headers={"Authorization": f"Bearer {settings.CAPTCHA_KEY}"}
        )
        if r.json().get("task_id") is None:
            raise Exception(f'Create captcha error: {r.json()}')

        return r.json()["task_id"]

    def get_result(self, task_id: str):
        for _ in range(400):
            r = get(
                url=f"{self.api_link}/status/{task_id}",
                headers={"Authorization": f"Bearer {settings.CAPTCHA_KEY}"}
            )

            if r.json().get("status") == "completed":
                return r.json()["result"]["solution"]

            elif r.json().get("status") not in ["pending", "running"]:
                error_text = r.json()
                raise Exception(f'Solve captcha error: {error_text}')

            sleep(5)

        raise Exception(f'Captcha expired')
