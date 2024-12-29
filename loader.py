import asyncio

from utils import load_config, FileOperations, Progress

config = load_config()
file_operations = FileOperations()
progress = Progress(len(config.accounts))
semaphore = asyncio.Semaphore(config.threads)
