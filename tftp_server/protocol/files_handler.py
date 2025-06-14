import asyncio
import os
from async_lru import alru_cache
import aiofiles
from enum import Enum

class FileType(Enum):
    online = 1  # File is available online
    on_disk = 2  # File is stored on disk

async def get_file_from_disk(file_path: str) -> bytes|None:
    """
    Fetch a file from the disk.
    :param file_path: Path to the file on disk.
    :return: File content as bytes, if path does not exist or is not a file or permission errors, return None.
    """
    if not (os.path.exists(file_path) and os.path.isfile(file_path) and os.access(file_path, os.R_OK)):
        return None 
    async with aiofiles.open(file_path, 'rb') as f:
        return await f.read()    

@alru_cache(maxsize=128)
async def get_file(file_type: FileType, file_path: str) -> bytes|None:
    if file_type == FileType.on_disk:
        return await get_file_from_disk(file_path)
    elif file_type == FileType.online:
        # Placeholder for online file fetching logic
        # This could be an HTTP request or any other method to fetch the file online
        pass
