import struct
from dataclasses import dataclass
from enum import Enum
from typing import Optional

class Opcode(Enum):
    RRQ = 1  # Read Request
    WRQ = 2  # Write Request
    DATA = 3  # Data Packet
    ACK = 4  # Acknowledgment
    ERROR = 5  # Error Packet

class ErrorCode(Enum):
    NOT_FOUND = 1  # File not found
    ACCESS_VIOLATION = 2  # Access violation
    DISK_FULL = 3  # Disk full or allocation exceeded
    ILLEGAL_OPERATION = 4  # Illegal TFTP operation
    UNKNOWN_TID = 5  # Unknown transfer ID
    FILE_EXISTS = 6  # File already exists
    NO_SUCH_USER = 7  # No such user

@dataclass(kw_only=True)
class TftpPacket:
    opcode: Optional[Opcode] = None

@dataclass
class RrqPacket(TftpPacket):
    """
    Read Request Packet
      Type   Op #     Format without header

          2 bytes    string   1 byte     string   1 byte
          -----------------------------------------------
   RRQ/  | 01/02 |  Filename  |   0  |    Mode    |   0  |
   WRQ    -----------------------------------------------
    """
    filename: str
    mode: str
    
    def __post_init__(self):
        self.opcode = Opcode.RRQ

    @property
    def get_bytes(self):
        return struct.pack(f"!H {len(self.filename)}s {len(self.mode)}s", 
                           self.opcode.value, 
                           (self.filename + '\0').encode(), 
                           (self.mode + '\0').encode())
    
@dataclass
class WrqPacket(TftpPacket):
    """
    Write Request Packet
      Type   Op #     Format without header

          2 bytes    string   1 byte     string   1 byte
          -----------------------------------------------
   RRQ/  | 01/02 |  Filename  |   0  |    Mode    |   0  |
   WRQ    -----------------------------------------------
    """
    filename: str
    mode: str
    
    def __post_init__(self):
        self.opcode = Opcode.WRQ

    @property
    def get_bytes(self):
        return struct.pack(f"!H {len(self.filename)}s {len(self.mode)}s", 
                           self.opcode.value, 
                           (self.filename + '\0').encode(), 
                           (self.mode + '\0').encode())
    
@dataclass
class DataPacket(TftpPacket):
    """
    Data Packet
    Type   Op #     Format without header
            2 bytes    2 bytes       n bytes
            ---------------------------------
    DATA  | 03    |   Block #  |    Data    |
            ---------------------------------

    """
    block: int
    data: bytes
    
    def __post_init__(self):
        self.opcode = Opcode.DATA

    @property
    def get_bytes(self):
        return struct.pack(f"!H H{len(self.data)}s", 
                           self.opcode.value, 
                           self.block, 
                           self.data)
    
@dataclass
class AckPacket(TftpPacket):
    """
    Type   Op #     Format without header
            2 bytes    2 bytes
            -------------------
    ACK   | 04    |   Block #  |
            --------------------
    """
    block: int
    
    def __post_init__(self):
        self.opcode = Opcode.ACK

    @property
    def get_bytes(self):
        return struct.pack("!H H", self.opcode.value, self.block)
    
@dataclass
class ErrorPacket(TftpPacket):
    """
    Type   Op #     Format without header 
            2 bytes  2 bytes        string    1 byte
            ----------------------------------------
    ERROR | 05    |  ErrorCode |   ErrMsg   |   0  |
            ----------------------------------------
    """
    error_code: ErrorCode
    error_message: str
    
    def __post_init__(self):
        self.opcode = Opcode.ERROR

    @property
    def get_bytes(self):
        return struct.pack(f"!H H {len(self.error_message)}s", 
                           self.opcode.value, 
                           self.error_code.value, 
                           (self.error_message + '\0').encode())

def parse_packet(data: bytes) -> TftpPacket:
    """
    Parse a TFTP packet from bytes.
    """
    try:
        opcode = struct.unpack("!H", data[:2])[0]
        
        if opcode == Opcode.RRQ.value:
            filename, mode = data[2:].split(b'\0')[:2]
            return RrqPacket(filename=filename.decode(), mode=mode.decode())
        
        elif opcode == Opcode.WRQ.value:
            filename, mode = data[2:].split(b'\0')[:2]
            return WrqPacket(filename=filename.decode(), mode=mode.decode())
        
        elif opcode == Opcode.DATA.value:
            block, = struct.unpack("!H", data[2:4])
            return DataPacket(block=block, data=data[4:])
        
        elif opcode == Opcode.ACK.value:
            block, = struct.unpack("!H", data[2:4])
            return AckPacket(block=block)
        
        elif opcode == Opcode.ERROR.value:
            error_code, = struct.unpack("!H", data[2:4])
            error_message = data[4:-1].decode()  # Exclude the null terminator
            return ErrorPacket(error_code=ErrorCode(error_code), error_message=error_message)
    except struct.error as e:
        return None        
