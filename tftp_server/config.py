from dataclasses import dataclass
import os

DEFAULT_PORT = 69
DEFAULT_MAX_BLOCK_SIZE = 512
DEFAULT_TIMEOUT = 1
DEFAULT_RETRIES = 3
DEFAULT_DIR = "/tmp/tftp"
DEFAULT_HOST = "0.0.0.0"

@dataclass
class TftpConfig:
    """
    Configuration for the TFTP server.
    """
    host: str = DEFAULT_HOST
    port: int = DEFAULT_PORT
    max_block_size: int = DEFAULT_MAX_BLOCK_SIZE
    timeout: int = DEFAULT_TIMEOUT
    retries: int = DEFAULT_RETRIES
    file_directory: str = DEFAULT_DIR
    single_port: bool = False

    def __post_init__(self):
        if not isinstance(self.port, int) or not (0 <= self.port <= 65535):
            raise ValueError("Port must be an integer between 0 and 65535.")
        if not isinstance(self.max_block_size, int) or self.max_block_size <= 0:
            raise ValueError("Max block size must be a positive integer.")
        if not isinstance(self.timeout, int) or self.timeout <= 0:
            raise ValueError("Timeout must be a positive integer.")
        if not isinstance(self.retries, int) or self.retries < 0:
            raise ValueError("Retries must be a non-negative integer.")
        if not isinstance(self.file_directory, str) or not self.is_directory_valid():
            raise ValueError("File directory must be a non-empty string and must exist.")
        
    def is_directory_valid(self):
        """
        Check if the file directory exists and is readable.
        """
        
        return os.path.isdir(self.file_directory) and os.access(self.file_directory, os.R_OK)