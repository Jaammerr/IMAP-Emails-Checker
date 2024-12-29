import asyncio
from typing import Literal

import aiofiles

from pathlib import Path

from loguru import logger

from models import ModuleType, OperationResult


class FileOperations:
    def __init__(self, base_path: str = "./results"):
        self.base_path = Path(base_path)
        self.lock = asyncio.Lock()
        self.module_paths: dict[ModuleType, dict[str, Path]] = {
            "check": {
                "success": self.base_path / "success.txt",
                "invalid_credentials": self.base_path / "invalid_credentials.txt",
                "connection_error": self.base_path / "connection_error.txt",
            },
        }

    async def setup_files(self):
        self.base_path.mkdir(exist_ok=True)
        for module_paths in self.module_paths.values():
            for path in module_paths.values():
                if path.exists():
                    path.unlink()
                path.touch()

    async def export_result(
        self,
        result: OperationResult,
        module: ModuleType,
        mode: Literal["default", "oauth2"],
    ):
        if module not in self.module_paths:
            raise ValueError(f"Unknown module: {module}")

        file_path = (
            self.module_paths[module]["success" if result.status else "failed"]
            if not result.error_type
            else self.module_paths[module][result.error_type]
        )
        async with self.lock:
            try:
                async with aiofiles.open(file_path, "a") as file:
                    if mode == "default":
                        await file.write(
                            f"{result.account.email}:{result.account.password}\n"
                        )
                    else:
                        await file.write(
                            f"{result.account.email}:{result.account.client_id}:{result.account.refresh_token}\n"
                        )
            except IOError as e:
                logger.error(
                    f"Email: {result.account.email} | Failed to write to file: {str(e)}"
                )
