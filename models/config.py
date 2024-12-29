from better_proxy import Proxy
from pydantic import BaseModel, PositiveInt, ConfigDict


class Account(BaseModel):
    email: str
    client_id: str = ""  # OAuth2
    refresh_token: str = ""  # OAuth2
    password: str = ""
    imap_server: str = ""


class Config(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    class Range(BaseModel):
        min: int
        max: int

    accounts: list[Account]
    proxies: list[Proxy]
    retry_limit: PositiveInt

    use_proxy: bool
    use_oauth: bool

    threads: PositiveInt
    imap_settings: dict[str, str]
    module: str = "checker"
