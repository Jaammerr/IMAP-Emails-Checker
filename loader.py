import asyncio

from utils import load_config, FileOperations

config = load_config()
file_operations = FileOperations()
semaphore = asyncio.Semaphore(config.threads)
