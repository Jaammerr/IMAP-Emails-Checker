import asyncio
import sys

from loguru import logger

from core.imap_checker import IMAPChecker


def run() -> None:
    try:
        IMAPChecker().run()
    except KeyboardInterrupt:
        pass

    except Exception as e:
        logger.error(f"Unhandled Error: {e}")


if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    run()
