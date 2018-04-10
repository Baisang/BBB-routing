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
    PAYLOAD:        payload string
    """
    ROUTEUPDATE = 1
    PAYLOAD = 2

PUBLIC_ENUMS = {
    'BBBPacketType': BBBPacketType
}

# JSON encoding and decoding helpers
class BBBPacketEncoder(json.JSONEncoder):
    def default(self, obj):
        if type(obj) in PUBLIC_ENUMS.values():
            return {"__enum__": str(obj)}
        return json.JSONEncoder.default(self, obj)

def as_enum(d):
    if "__enum__" in d:
        name, member = d["__enum__"].split(".")
        return getattr(PUBLIC_ENUMS[name], member)
    else:
        return d

# Packet class for BBB Routing
class BBBPacket(object):
    def __init__(self, src, dst, type, payload):
        """
        Constructor for a BBBPacket
        @src                    address of source
        @dest                   address of destination
        @type BBBPacketType     A BBBPacket Type
        @payload                string payload
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
            "src": self.src,
            "dst": self.dst,
            "type": self.type,
            "payload": self.payload
        }, cls=BBBPacketEncoder)
        return json_serialization.encode()

    @classmethod
    def from_bytes(cls, bytes, object_hook=as_enum):
        """
        @bytes      byte representation of this class
        @return     BBBPacket instance corresponding to bytes
        """
        data = json.loads(bytes.decode(), object_hook=as_enum)
        return cls(**data)


class RouterBase(object):
    def __init__(self, address):
        self.routes = {}
        self.socket = socket.socket()
        self.socket.bind((address, ROUTER_PORT))
        self.socket.listen()

    def update_routes(packet):
        self.routes.update(packet.payload)
