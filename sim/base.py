import select
import socket
import sys
import threading
import json
from threading import Lock
from Crypto.PublicKey import RSA
from bigchaindb_driver import BigchainDB
from bigchaindb_driver.crypto import CryptoKeypair
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
    FLOOD:          Data packet sent using robust flooding
    """
    MASTERCONFIG = 0
    ROUTEUPDATE = 1
    FLOOD = 2

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
    def __init__(self, src, dst, type, payload, seq, signature=None):
        """
        Constructor for a BBBPacket
        @src                    address of source
        @dst                   address of destination
        @type BBBPacketType     A BBBPacket Type
        @payload                string payload
        @seq                    sequence number
        """
        self.src = src
        self.dst = dst
        self.type = type
        self.payload = payload
        self.seq = seq
        if signature:
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
    def __init__(self, ip_address, test=False):
        self.routes = {}        # dst_ip: next_hop_ip
        self.sockets = {}       # next_hop_ip: socket_instance
        self.keys = {}          # ip: packet_public_key
        self.sqn_numbers = {}   # ip: most recent sequence number received
        self.neighbors = set()  # ip addresses of neighbors
        self.hosts = []         # any hosts attached to this router
        self.buffer_lock = Lock()

        # For unit tests
        self.test = test

        # Key used for signing packets
        self.packet_key = RSA.generate(2048)

        # Connect to bigchaindb
        if not test:
            bdb_root_url = 'http://localhost:9984' # TODO: is this right?
            self.bdb = BigchainDB(bdb_root_url)
            # Read bdb keypair from the .bigchaindb config file
            with open('build/.bigchaindb') as f:
                d = json.load(f)
            self.bdb_keypair = CryptoKeypair(
                    d['keypair']['private'],
                    d['keypair']['public'],
            )
            self.keyring = d['keyring']

            # Add packet public key, IP addr to bigchaindb
            asset = {'data':
                        {
                            'public_key': self.packet_key.publickey().export_key().decode(),
                            'ip_address': ip_address,
                        },
                    }
            prepared_transaction = self.bdb.transactions.prepare(
                operation = 'CREATE',
                signers = self.bdb_keypair.public_key,
                asset = asset,
            )
            fulfilled_transaction = self.bdb.transactions.fulfill(
                prepared_transaction,
                private_keys = self.bdb_keypair.private_key,
            )
            sent_txn = self.bdb.transactions.send(fulfilled_transaction)


            self.socket = socket.socket()
            self.socket.bind((ip_address, ROUTER_PORT))
            self.socket.listen()
        self.ip_address = ip_address
        print("starting server on {0}:{1}".format(ip_address, ROUTER_PORT))
