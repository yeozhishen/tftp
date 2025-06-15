from tftp_server.config import *
from tftp_server.tftp_server import TftpServer
import logging
import argparse

def parse_args():
    """
    Parse command-line arguments for the TFTP server configuration.
    """
    parser = argparse.ArgumentParser(description="Run the TFTP server.")
    parser.add_argument("--host", type=str, default=DEFAULT_HOST, help="Host to bind the TFTP server (default: 0.0.0.0)")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help="Port to bind the TFTP server (default: 69)")
    parser.add_argument("--max-block-size", type=int, default=DEFAULT_MAX_BLOCK_SIZE, help="Maximum block size for file transfers (default: 512)")
    parser.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT, help="Timeout in seconds for client responses (default: 1)")
    parser.add_argument("--retries", type=int, default=DEFAULT_RETRIES, help="Number of retries for failed transfers (default: 3)")
    parser.add_argument("--file-directory", type=str, default=DEFAULT_DIR, help="Directory to serve files from (default: /tmp/tftp)")
    return parser.parse_args()


def main():
    args = parse_args()
    config = TftpConfig(
        host=args.host,
        port=args.port,
        max_block_size=args.max_block_size,
        timeout=args.timeout,
        retries=args.retries,
        file_directory=args.file_directory,
    )
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("TFTPServer")
    server = TftpServer(config, logger=logger)
    server.start()

if __name__ == "__main__":
    main()