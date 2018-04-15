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
    MASTERCONFIG:   Packet from MASTER configuring network topology
    ROUTEUPDATE:    Updates about network topology
    PAYLOAD:        payload string, sent after a ROUTESETUP
    """
    MASTERCONFIG = 0
    ROUTEUPDATE = 1
    PAYLOAD = 2

PUBLIC_ENUMS = {
    'BBBPacketType': BBBPacketType
}

class BBBPacketEncoder(json.JSONEncoder):
    """Serializing Class to turn BBBPackets into a JSON string
    """
    def default(self, obj):
        if type(obj) in PUBLIC_ENUMS.values():
            return {"__enum__": str(obj)}
        return json.JSONEncoder.default(self, obj)

def as_enum(d):
    """Helper for deserializing a valid JSON string back into a BBBPacket.
    """
    if "__enum__" in d:
        name, member = d["__enum__"].split(".")
        return getattr(PUBLIC_ENUMS[name], member)
    else:
        return d

def pad(message):
    """Pads packet payloads to specific length using a PAD_CHAR
    """
    return message + (PACKET_LEN - len(message)) * PAD_CHAR

def unpad(message):
    """Removes packet padding
    """
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
    """Base Class for this Router.
    """
    def __init__(self, ip_address):
        self.routes = {}        # dst_ip: next_hop_ip
        self.sockets = {}       # next_hop_ip: socket_instance
        self.keys = {}          # ip: public_key
        self.neighbors = set()  # ip addresses of neighbors

        self.socket = socket.socket()
        self.socket.bind((ip_address, ROUTER_PORT))
        self.socket.listen()
        self.ip_address = ip_address
        print("starting server on {0}:{1}".format(address, ROUTER_PORT))
