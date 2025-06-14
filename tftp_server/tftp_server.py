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
    
    async def listen(self) -> None:
        self.transport, self.protocol = await asyncio.get_running_loop().create_datagram_endpoint(
            lambda: TftpServerProtocol(self, logger=self.logger),
            local_addr=(self.config.host, self.config.port)
        )
        self.logger.info(f"TFTP server listening on {self.config.host}:{self.config.port}")
        try:
            await asyncio.Event().wait()  # Wait forever
        finally:
            self.transport.close()
        
    
    def start(self) -> None:
        try:
            self.logger.info(f"Starting TFTP server on {self.config.host}:{self.config.port}")
            asyncio.run(self.listen())
        except KeyboardInterrupt:
            self.logger.info("TFTP server stopped by user")
    