from typing import Optional, Union
from itertools import cycle
import asyncio
from contextlib import asynccontextmanager

from imaplib import IMAP4_SSL
import httpx
from better_proxy import Proxy
from imap_tools import MailBox as BaseMailBox, MailboxLoginError

from loguru import logger

from utils.imap_utils import IMAP4SSlProxy
from models import Account, OperationResult
from loader import file_operations, config, progress, semaphore


class MailBoxClient(BaseMailBox):
    def __init__(
        self,
        host: str,
        proxy: Union[Proxy, str] = None,
        port: int = 993,
        timeout: float = 10,
        rdns: bool = True,
        ssl_context=None,
    ):
        self._proxy = Proxy.from_str(proxy) if isinstance(proxy, str) else proxy
        self._rdns = rdns
        super().__init__(host=host, port=port, timeout=timeout, ssl_context=ssl_context)

    def _get_mailbox_client(self):
        client_class = IMAP4SSlProxy if self._proxy else IMAP4_SSL
        client_kwargs = {
            "host": self._host,
            "port": self._port,
            "timeout": self._timeout,
            "ssl_context": self._ssl_context,
        }

        if self._proxy:
            client_kwargs.update(
                {
                    "proxy": self._proxy,
                    "rdns": self._rdns,
                }
            )

        return client_class(**client_kwargs)


class OAuthAuthenticator:
    TOKEN_URL = "https://login.microsoftonline.com/common/oauth2/v2.0/token"

    def __init__(self, account: Account):
        self.account = account

    @asynccontextmanager
    async def _get_client(self, proxy: Optional[str] = None):
        async with httpx.AsyncClient(
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            proxy=proxy,
            timeout=10,
        ) as client:
            yield client

    async def get_access_token(self, current_proxy: Optional[Proxy] = None) -> str:
        try:
            proxy = current_proxy.as_url if config.use_proxy and current_proxy else None

            async with self._get_client(proxy) as client:
                response = await client.post(
                    self.TOKEN_URL,
                    data={
                        "client_id": self.account.client_id,
                        "refresh_token": self.account.refresh_token,
                        "grant_type": "refresh_token",
                    },
                )
                response.raise_for_status()
                return response.json()["access_token"]

        except Exception as error:
            validated_error = self._clean_error_message(str(error))
            logger.error(
                f"Failed to retrieve Microsoft access token for {self.account.email}: {validated_error}"
            )
            raise Exception(validated_error)

    @staticmethod
    def _clean_error_message(error: str) -> str:
        return error.replace(
            "For more information check: https://developer.mozilla.org/en-US/docs/Web/HTTP/Status/400",
            "",
        ).strip()


class IMAPChecker:
    def __init__(self):
        self.proxy_cycle = cycle(config.proxies) if config.proxies else None
        self.oauth_authenticator: Optional[OAuthAuthenticator] = None

    def _get_next_proxy(self) -> Optional[Proxy]:
        return next(self.proxy_cycle) if self.proxy_cycle else None

    @staticmethod
    def show_progress():
        progress.increment()
        logger.info(f"Progress: {progress.processed}/{progress.total}")

    async def _authenticate_mailbox(
        self, mailbox: MailBoxClient, account: Account, current_proxy: Optional[Proxy]
    ):
        if account.refresh_token:
            self.oauth_authenticator = OAuthAuthenticator(account)
            access_token = await self.oauth_authenticator.get_access_token(
                current_proxy
            )
            await asyncio.to_thread(
                lambda: mailbox.xoauth2(account.email, access_token)
            )
        else:
            await asyncio.to_thread(
                lambda: mailbox.login(account.email, account.password)
            )

    async def _check_single_account(self, account: Account) -> OperationResult:
        logger.info(f"Checking email: {account.email}..")
        current_proxy = self._get_next_proxy() if config.use_proxy else None

        for attempt in range(config.retry_limit):
            try:
                mailbox = await asyncio.to_thread(
                    lambda: MailBoxClient(
                        host=account.imap_server,
                        proxy=str(current_proxy) if current_proxy else None,
                    )
                )

                await self._authenticate_mailbox(mailbox, account, current_proxy)

                logger.success(f"Email: {account.email} | Email valid")
                self.show_progress()

                return OperationResult(status=True, account=account)

            except MailboxLoginError:
                logger.error(
                    f"Email: {account.email} | Email invalid: Invalid credentials"
                )
                self.show_progress()
                return OperationResult(
                    status=False,
                    error="Invalid credentials",
                    error_type="invalid_credentials",
                    account=account,
                )

            except Exception as e:
                if attempt + 1 == config.retry_limit:
                    error_msg = (
                        f"Connection failed after all attempts | Last error: {str(e)}"
                    )
                    logger.error(f"Email: {account.email} | Email invalid: {error_msg}")
                    self.show_progress()
                    return OperationResult(
                        status=False,
                        error=error_msg,
                        error_type="connection_error",
                        account=account,
                    )

                logger.error(
                    f"Email: {account.email} | Proxy failed: {str(e)} | "
                    f"Switching to next proxy.. | Attempt {attempt + 1}/{config.retry_limit}"
                )
                current_proxy = self._get_next_proxy()

    async def check_single_account_safe(self, account: Account):
        async with semaphore:
            return await self._check_single_account(account)

    async def check_accounts(self):
        tasks = [
            asyncio.create_task(self.check_single_account_safe(account))
            for account in config.accounts
        ]

        for completed_task in asyncio.as_completed(tasks):
            result = await completed_task
            await file_operations.export_result(
                result=result,
                module="check",
                mode="oauth2" if result.account.refresh_token else "default",
            )
