import asyncio
from typing import Optional
from itertools import cycle
from datetime import datetime

from imaplib import IMAP4_SSL
from better_proxy import Proxy
from imap_tools import MailBox as BaseMailBox, MailboxLoginError
from concurrent.futures import ThreadPoolExecutor, as_completed

from loguru import logger

from .imap_utils import IMAP4SSlProxy
from models import Account, OperationResult
from loader import file_operations, config



class MailBoxClient(BaseMailBox):
    def __init__(
        self,
        host: str,
        *,
        proxy: Proxy | str = None,
        port: int = 993,
        timeout: float = None,
        rdns: bool = True,
        ssl_context=None,
    ):
        self._proxy = Proxy.from_str(proxy) if proxy else None
        self._rdns = rdns
        super().__init__(host=host, port=port, timeout=timeout, ssl_context=ssl_context)

    def _get_mailbox_client(self):
        if self._proxy:
            return IMAP4SSlProxy(
                self._host,
                self._proxy,
                port=self._port,
                rdns=self._rdns,
                timeout=self._timeout,
                ssl_context=self._ssl_context,
            )
        else:
            return IMAP4_SSL(
                self._host,
                port=self._port,
                timeout=self._timeout,
                ssl_context=self._ssl_context,
            )


class IMAPChecker:
    def __init__(self):
        self.proxy_cycle = cycle(config.proxies) if config.proxies else None

    def _get_next_proxy(self) -> Optional[Proxy]:
        return next(self.proxy_cycle)

    def _check_single_account(self, account: Account) -> OperationResult:
        current_proxy = self._get_next_proxy()

        for attempt in range(config.retry_limit):
            try:
                with MailBoxClient(
                    host=account.imap_server,
                    proxy=str(current_proxy) if current_proxy else None,
                    timeout=30
                ).login(account.email, account.password):
                    return {
                        "status": True,
                        "identifier": account.email,
                        "password": account.password,
                        "data": f"Success:{datetime.now()}"
                    }

            except MailboxLoginError:
                return {
                    "status": False,
                    "identifier": account.email,
                    "password": account.password,
                    "data": "Invalid credentials"
                }

            except Exception as e:
                if attempt + 1 == config.retry_limit:
                    return {
                        "status": False,
                        "identifier": account.email,
                        "password": account.password,
                        "data": "Connection failed after all attempts | Last error: " + str(e)
                    }

                logger.error(f"Email: {account.email} | Proxy failed: {str(e)} | Switching to next.. | Attempt {attempt + 1}/{config.retry_limit}")
                current_proxy = self._get_next_proxy()
                continue


    async def check_accounts(self):
        await file_operations.setup_files()

        with ThreadPoolExecutor(max_workers=config.threads) as executor:
            future_to_account = {
                executor.submit(self._check_single_account, account): account
                for account in config.accounts
            }

            for future in as_completed(future_to_account):
                result = future.result()
                await file_operations.export_result(result, "check")

                if result["status"]:
                    logger.success(f"Email: {result['identifier']} | Successfully checked")
                else:
                    logger.error(f"Email: {result['identifier']} | Failed to check: {result['data']}")

    def run(self):
        asyncio.run(self.check_accounts())
