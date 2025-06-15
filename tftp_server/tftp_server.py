import asyncio
from tftp_server.config import TftpConfig
import logging
from tftp_server.protocol.protocol import TftpServerProtocol
    
class TftpServer():
    def __init__(self, config: TftpConfig, logger: logging.Logger = None):
        self.config = config
        self.transport = None
        self.protocol = None
        self.logger = logger
    
    def listen(self) -> None:
        endpoint = (event_loop := asyncio.get_event_loop()).create_datagram_endpoint(
            lambda: TftpServerProtocol(self, logger=self.logger),
            local_addr=(self.config.host, self.config.port)
        )
        self.logger.info(f"TFTP server listening on {self.config.host}:{self.config.port}")
        event_loop.run_until_complete(endpoint)
        event_loop.run_forever()
    
    
    def start(self) -> None:
        try:
            self.listen()
        except KeyboardInterrupt:
            self.logger.info("TFTP server stopped by user")
    