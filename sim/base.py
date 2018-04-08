import select
import socket
import sys
import json
from enum import Enum


DEBUG = True
ROUTER_PORT = 42425
PACKET_LEN = 2048

class BBBPacketType(Enum):
    """
    Enum for different BBBPacket types
    ROUTEUPDATE:    Upadtes about network topology
    PAYLOAD:        Raw data to be delivered
    """
    ROUTEUPDATE = 1
    PAYLOAD = 2


class BBBPacket(object):
    def __init__(self, src, dst, type, payload):
        """
        Constructor for a BBBPacket
        @src                    address of source
        @dest                   address of destination
        @type BBBPacketType     A BBBPacket Type
        @payload                raw data in bytes
        """
        self.src = src
        self.dst = dst
        self.type = type
        self.payload = payload

    def to_bytes(self):
        """
        @return     byte representation of this class
        """
        json_serialization = json.dumps({
            "type": self.type,
            "payload": self.payload
        })
        return json_serialization.encode()

    @classmethod
    def from_bytes(cls, bytes):
        """
        @bytes      byte representation of this class
        @return     BBBPacket instance corresponding to bytes
        """
        data = json.loads(bytes.decode())
        return BBBPacket(**data)


class RouterBase(object):
    def __init__(self, address):
        self.routes = {}
        self.socket = socket.socket()
        self.socket.bind((address, ROUTER_PORT))
        self.socket.listen()

    def update_routes(packet):
        self.routes.update(packet.payload)
