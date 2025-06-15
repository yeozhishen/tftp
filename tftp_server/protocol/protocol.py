import asyncio
import logging
from tftp_server.protocol import packets
from enum import Enum
from dataclasses import dataclass
from tftp_server.protocol.files_handler import get_file, FileType

MAX_BLOCK_VALUE = 65535

@dataclass
class TftpCounters:
    """
    Class to hold counters for the TFTP server i.e. number of retrie and any other counters that might be needed.
    """
    retries: int = 0  # Number of retries for the current request

    def reset(self):
        """
        Reset the counters to their initial values.
        """
        self.retries = 0

@dataclass
class StateConfig:
    """
    Base Configuration for ephemeral connections states
    """
    filename: str
    mode: str
    block: int = 1

    def __post_init__(self):
        if not isinstance(self.filename, str) or not self.filename:
            raise ValueError("Filename must be a non-empty string.")
        if not isinstance(self.mode, str) or self.mode not in ["octet", "netascii"]:
            raise ValueError("Mode must be either 'octet' or 'netascii'.")

@dataclass
class RrqConfig(StateConfig):
    """
    Configuration for the RRQ state.
    """
    file_data: str = None  # filedata to send to the client (will be loading everything in memory)
    file_size: int = None
    block_overflows: int = 0  # number of times the block overflows in the protocol, as it is only 16 bits

class ServerStates(Enum):
    """
    Enum representing the states of the TFTP server.
    """
    INITIAL = 0
    RRQ = 1
    WRQ = 2
    ERROR = 3
    # state to indicate that the client should be killed
    KILL = 4

class TftpServerProtocol(asyncio.DatagramProtocol):
    def __init__(self, server, logger: logging.Logger = None):
        self.server = server
        self.logger = logger
        self.transport = None

    def connection_made(self, transport) -> None:
        self.transport = transport
        self.logger.info(f"TFTP socket initialized and listening on {self.server.config.host}:{self.server.config.port}")

    def datagram_received(self, data: bytes, addr) -> None:
        self.logger.info(f"Received data from {addr}: {data}")
        try:
            asyncio.create_task(
                asyncio.get_running_loop().create_datagram_endpoint(
                    lambda: TftpEphemeralPortProtocol(base_file_dir=self.server.config.file_directory, 
                                                      client_ip=addr[0], client_port=addr[1], 
                                                      initial_data=data, logger=self.logger,
                                                      file_block_size=self.server.config.max_block_size
                                                      , timeout=self.server.config.timeout,
                                                      retries=self.server.config.retries),
                    local_addr=(self.server.config.host, 0) # binds to an ephemeral port
                )
            )
            
        except Exception as e:
            self.logger.error(f"Error creating ephemeral port protocol: {e}")
            return        

class TftpEphemeralPortProtocol(asyncio.DatagramProtocol):
    def __init__(self, file_block_size: int, base_file_dir: str, client_ip: str
                 , client_port: int, initial_data:bytes, timeout:int, retries:int, logger: logging.Logger = None):
        self.logger = logger
        self.base_file_dir: str = base_file_dir 
        self.client_ip:int = client_ip
        self.client_port: int = client_port
        self.initial_data: bytes = initial_data
        self.transport: asyncio.transports = None
        self.state: ServerStates = ServerStates.INITIAL
        self.state_config: StateConfig = None
        self.block_size: int = file_block_size
        self.timeout:int = timeout
        self.max_retries: int = retries
        self._counters: TftpCounters = TftpCounters()  # Counters for the TFTP server
        self._timeout_handle: asyncio.Handle | None = None  # Handle for the timeout task 

    def connection_made(self, transport) -> None:
        self.transport = transport
        self.logger.info(f"Ephemeral port socket initialized and listening on {transport.get_extra_info('sockname')} ")
        self.handle_new_connection()

    def datagram_received(self, data: bytes, addr) -> None:
        self.logger.info(f"Received ephemeral port request from {addr}: {data}")
        packet = packets.parse_packet(data)
        if packet is None:
            self.logger.error(f"Failed to parse packet from {addr}")
            # unknow packet type, close the connnection since client is not following the protocol
            self.transport.close()
            return
        # Handle the request and send a response
        self._reset_timeout()
        self._counters.reset()  # Reset the counters for each new packet received
        if self.state == ServerStates.RRQ and packet.opcode == packets.Opcode.ACK:
            self.logger.info(f"Handling RRQ continuation for {self.state_config.filename} in mode {self.state_config.mode}")
            self.handle_rrq_connection(packet, addr)
        elif self.state == ServerStates.WRQ and packet.opcode == packets.Opcode.DATA:
            self.logger.info(f"Handling WRQ continuation for {self.state_config.filename} in mode {self.state_config.mode}")
            self.send_error(packets.ErrorCode.ILLEGAL_OPERATION, "Write requests are not supported yet")
        elif self.state == ServerStates.KILL:
            self.logger.info(f"ephemeral port feature is complete, killing socket")
            self.transport.close()
        else:
            self.logger.error(f"Received data in unexpected state {self.state} from {addr}")
            self.send_error(packets.ErrorCode.ILLEGAL_OPERATION, "Unexpected state for received data")
            
    def send_error(self, error_code: packets.ErrorCode, error_message: str) -> None:
        self.state = ServerStates.ERROR
        error_packet = packets.ErrorPacket(error_code, error_message)
        self.transport.sendto(error_packet.get_bytes, (self.client_ip, self.client_port))
        self.logger.error(f"Sent error packet to {self.client_ip}:{self.client_port} with code {error_code} and message '{error_message}'")
        self.transport.close()

    def handle_new_connection(self) -> None:
        initial_packet = packets.parse_packet(self.initial_data)
        if initial_packet is None:
            self.logger.error("Failed to parse initial packet")
            self.transport.close()
            return
        if initial_packet.opcode == packets.Opcode.RRQ:
            self.logger.info(f"Received RRQ from {self.client_ip}:{self.client_port} for file: {initial_packet.filename}")
            self.state = ServerStates.RRQ
            try:
                self.state_config = RrqConfig(filename=initial_packet.filename, mode=initial_packet.mode)
                #get the file data
                get_file_task = asyncio.create_task(
                    get_file(FileType.on_disk, f"{self.base_file_dir}/{self.state_config.filename}")
                )
                get_file_task.add_done_callback(self._handle_get_file_task_result)
            except ValueError as e:
                self.send_error(packets.ErrorCode.ILLEGAL_OPERATION, str(e))
                return
        elif initial_packet.opcode == packets.Opcode.WRQ:
            self.logger.info(f"Received WRQ from {self.client_ip}:{self.client_port} for file: {initial_packet.Filename}")
            # Handle Write Request
            # TODO: Implement file write logic
            self.state = ServerStates.WRQ
        else:
            self.logger.error(f"Unsupported opcode {initial_packet.opcode} from {self.client_ip}:{self.client_port}")
            self.state = ServerStates.ERROR           
            self.transport.close()
            return

    def _handle_get_file_task_result(self, future: asyncio.Future) -> None:
        """
        Handles the first time the client makes a request to the server and the file is fetched.
        """
        file_data:bytes = future.result()
        if file_data is None:
            self.logger.error(f"File {self.state_config.filename} not found or inaccessible")
            self.send_error(packets.ErrorCode.NOT_FOUND, f"File {self.state_config.filename} not found")
            return
        self.state_config.file_data = file_data
        self.state_config.file_size = len(file_data)
        self.logger.info(f"File {self.state_config.filename} loaded successfully, sending data to client")
        self.send_data_block()
        # Send the first block of data

    def send_data_block(self):
        """
        Send a block of data to the client.
        precondition: self.state_config.file_data is not None, self.state is ServerStates.RRQ and self.state_config.block is a valid block number.
        """
        start = (self.state_config.block - 1) * self.block_size
        if self.state_config.block_overflows > 0:
            # the first time he protocol starts the block starts with 1 but when it overflows, it should start with 0
            # although the protocol is not meant to be used with files of this size since the protocol is stop and wait
            # to account for the overflows > 1 
            start = (self.state_config.block_overflows - 1) * self.block_size * (MAX_BLOCK_VALUE + 1)
            # to accound for the first overflow since the index starts at 1 for the first block
            start += self.block_size * MAX_BLOCK_VALUE
            start += self.state_config.block * self.block_size
        end = start + self.block_size
        if start < self.state_config.file_size:
            data_block = self.state_config.file_data[start:min(end, self.state_config.file_size)]
        else:
            data_block = "".encode()  # No more data to send, send an empty block to kill the connection
        data_packet = packets.DataPacket(block=self.state_config.block, data=data_block)
        self.transport.sendto(data_packet.get_bytes, (self.client_ip, self.client_port))
        self.logger.info(f"Sent block {self.state_config.block} to {self.client_ip}:{self.client_port}")        
        # Increment the block number for the next packet
        if self.state_config.block >= MAX_BLOCK_VALUE:
            self.state_config.block_overflows += 1
        self.state_config.block = (self.state_config.block + 1) % (MAX_BLOCK_VALUE + 1)
        if end > self.state_config.file_size: self.state = ServerStates.KILL

    def handle_rrq_connection(self, packet: packets.AckPacket, addr) -> None:
        """
        Handle RRQ continuation, when the server starts to request for more data packets.
        """
        # check if the address matches the client address
        if addr[0] != self.client_ip or addr[1] != self.client_port:
            self.logger.error(f"Received RRQ from unexpected address {addr}, expected {self.client_ip}:{self.client_port}")
            """
            RFC1350: When the first response arrives, host A continues the
            connection.  When the second response to the request arrives, it
            should be rejected, but there is no reason to terminate the first
            connection.  Therefore, if different TID's are chosen for the two
            connections on host B and host A checks the source TID's of the
            messages it receives, the first connection can be maintained while
            the second is rejected by returning an error packet.
            """
            self.send_error(packets.ErrorCode.UNKNOWN_TID, "Unexpected client address")
            return
        if packet.block == (self.state_config.block - 1) % (MAX_BLOCK_VALUE + 1):
            self.send_data_block()    
        else:
            self.logger.warning(f"Received ACK for block {packet.block} but expected block {(self.state_config.block - 1) % (MAX_BLOCK_VALUE + 1)}")

    def _cancel_timeout(self):
        """
        Cancel the timeout task if it exists.
        """
        if self._timeout_handle:
            self._timeout_handle.cancel()
            self._timeout_handle = None    

    def _reset_timeout(self):
        """
        Reset the timeout task to the initial timeout value.
        """
        self._cancel_timeout()
        self._timeout_handle = asyncio.get_event_loop().call_later(self.timeout, self._handle_timeout)

    def _handle_timeout(self):
        """
        Handle the timeout event.
        If the maximum number of retries is reached, close the connection.
        Otherwise, resend the last data block.
        """
        if self._counters.retries > self.max_retries:
            self.logger.error(f"Maximum retries reached for {self.client_ip}:{self.client_port}, closing connection")
            # do not need to send a packet becasue the conenction is assumed to be dead
            self.transport.close()
            return
        self.logger.warning(f"Timeout reached for {self.client_ip}:{self.client_port}, resending block {self.state_config.block - 1}")
        if self.state == ServerStates.RRQ:
            self._handle_rrq_timeout()
        elif self.state == ServerStates.WRQ:
            self.send_error(packets.ErrorCode.ILLEGAL_OPERATION, "Write requests are not supported yet")
            return
        else:
            self.logger.error(f"Timeout in unexpected state {self.state} for {self.client_ip}:{self.client_port}")
            self.transport.close()
            return
        self._counters.retries += 1
        self._reset_timeout()

    def _handle_rrq_timeout(self):
        """
        Handle the timeout event for RRQ state.
        If the maximum number of retries is reached, close the connection.
        Otherwise, resend the last data block.
        """
        if self.state_config.block == 0 and self.state_config.block_overflows > 0:
            self.state_config.block_overflows -= 1
            self.state_config.block = MAX_BLOCK_VALUE
        else:
            self.state_config.block -= 1
        self.send_data_block()

    def connection_lost(self, exc):
        self.logger.info(f"Closing connection with {self.client_ip}:{self.client_port}")
        self._cancel_timeout()
        return super().connection_lost(exc)
        

    