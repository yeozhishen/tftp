from tftp_server.config import TftpConfig
from tftp_server.tftp_server import TftpServer
import logging
def main():
    config = TftpConfig()
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("TFTPServer")
    server = TftpServer(config, logger=logger)
    server.start()

if __name__ == "__main__":
    main()