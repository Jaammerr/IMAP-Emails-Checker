from typing import Literal
from pydantic import BaseModel
from .config import Account

ModuleType = Literal["check"]


class OperationResult(BaseModel):
    status: bool
    error: str = ""
    error_type: Literal["connection_error", "invalid_credentials"] = ""
    account: Account
