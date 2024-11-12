from typing import Literal, TypedDict


ModuleType = Literal["check"]


class OperationResult(TypedDict):
    identifier: str
    password: str
    data: str
    status: bool
