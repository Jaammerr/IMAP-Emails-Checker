from better_proxy import Proxy
from pydantic import BaseModel, PositiveInt, ConfigDict


class Account(BaseModel):
    email: str
    password: str
    imap_server: str = ""


class Config(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    accounts: list[Account]
    proxies: list[Proxy]
    retry_limit: PositiveInt

    threads: PositiveInt
    imap_settings: dict[str, str]
