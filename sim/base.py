import select
import socket
import sys
import json
from enum import Enum


DEBUG = True
ROUTER_PORT = 42425
PACKET_LEN = 1024
PAD_CHAR = "~"

class BBBPacketType(Enum):
    """
    Enum for different BBBPacket types
    KEY:            Packet containing key information
    ROUTEUPDATE:    Updates about network topology
    ROUTESETUP:     Packet to setup route flow a certain flow
    PAYLOAD:        payload string, sent after a ROUTESETUP
    """
    KEY = 0
    ROUTEUPDATE = 1
    ROUTESETUP = 2
    PAYLOAD = 3


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

def pad(message):
    return message + (PACKET_LEN - len(message)) * PAD_CHAR

def unpad(message):
    return message.rstrip(PAD_CHAR)

# Packet class for BBB Routing
class BBBPacket(object):
    def __init__(self, src, dst, type, payload, seq, signature):
        """
        Constructor for a BBBPacket
        @src                    address of source
        @dest                   address of destination
        @type BBBPacketType     A BBBPacket Type
        @payload                string payload
        @seq                    sequence number
        @signature              signature
        """
        self.src = src
        self.dst = dst
        self.type = type
        self.payload = payload
        self.seq = seq
        self.signature = signature

    def to_bytes(self):
        """
        @return     byte representation of this class
        """
        json_serialization = json.dumps(
            vars(self),
            cls=BBBPacketEncoder
        )
        return pad(json_serialization).encode()

    @classmethod
    def from_bytes(cls, bytes, object_hook=as_enum):
        """
        @bytes      byte representation of this class
        @return     BBBPacket instance corresponding to bytes
        """
        data = json.loads(unpad(bytes.decode()), object_hook=as_enum)
        return cls(**data)


class RouterBase(object):
    def __init__(self, address):
        self.routes = {}
        self.neighbors = set()
        self.sockets = {}
        self.socket = socket.socket()
        self.socket.bind((address, ROUTER_PORT))
        self.socket.listen()
        self.address = address
        print("starting server on {0}:{1}".format(address, ROUTER_PORT))

    def update_routes(packet):
        self.routes.update(packet.payload)
