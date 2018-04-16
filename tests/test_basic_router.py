import sim

from sim.base import BBBPacket, BBBPacketType, pad, unpad
from sim.basic_router import BasicRouter

import unittest

from Crypto.Signature import pss
from Crypto.PublicKey import RSA

class TestBasicRouterCrypto(unittest.TestCase):

    def test_simple_sign_verify(self):
        router = BasicRouter('1.1.1.1', test=True)
        message = 'hello world'
        padded_message = pad(message)
        packet = BBBPacket('1.1.1.1', '2.2.2.2', BBBPacketType.PAYLOAD, padded_message, 0) 
        
        router.sign(packet)

        router.keys['1.1.1.1'] = router.packet_key.publickey()
        assert router.verify(packet)

        router.keys['1.1.1.1'] = RSA.generate(2048).publickey()
        assert not router.verify(packet)


