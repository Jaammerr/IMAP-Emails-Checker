import asyncio
import sys

from loguru import logger
from console import Console
from core.checker import IMAPChecker
from loader import file_operations
from utils import setup


async def run() -> None:
    try:
        await file_operations.setup_files()

        while True:
            module = Console().build()
            if module == "checker":
                await IMAPChecker().check_accounts()

            input("\n\nAll accounts checked, press enter to continue...")

    except KeyboardInterrupt:
        pass

    except Exception as e:
        logger.error(f"Unhandled Error: {e}")


if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    setup()
    asyncio.run(run())
