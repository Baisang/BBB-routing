import sim

from sim.base import BBBPacket, BBBPacketType
from sim.basic_router import BasicRouter

import json
import unittest
import threading
from unittest.mock import Mock
from Crypto.Signature import pss
from Crypto.PublicKey import RSA

class TestBasicRouter(unittest.TestCase):

    def test_simple_sign_verify(self):
        router = BasicRouter('1.1.1.1', test=True)
        message = 'hello world'
        packet = BBBPacket('1.1.1.1', '2.2.2.2', BBBPacketType.FLOOD, message, 0)

        router.sign(packet)

        router.keys['1.1.1.1'] = router.packet_key.publickey()
        assert router.verify(packet)

        router.keys['1.1.1.1'] = RSA.generate(2048).publickey()
        assert not router.verify(packet)

    def test_verify_sequence_number(self):
        router = BasicRouter('1.1.1.1', test=True)
        message = 'hello world'

        packet = BBBPacket('1.1.1.1', '2.2.2.2', BBBPacketType.FLOOD, message, 0)

        router.sign(packet)

        router.keys['1.1.1.1'] = router.packet_key.publickey()
        assert router.verify(packet)

        # Sequence number is the same, so we should reject this packet.
        packet2 = BBBPacket('1.1.1.1', '2.2.2.2', BBBPacketType.FLOOD, message, 0)
        router.sign(packet2)
        assert not router.verify(packet2)
        # Sequence number is higher, so we should accept this packet.
        packet3 = BBBPacket('1.1.1.1', '2.2.2.2', BBBPacketType.FLOOD, message, 1)
        router.sign(packet3)
        assert router.verify(packet3)

    def test_handle_flood_receive(self):
        router1 = BasicRouter('1.1.1.1', test=True)
        router2 = BasicRouter('2.2.2.2', test=True)
        router1.neighbors.add('2.2.2.2')
        router1.neighbors.add('3.3.3.3')
        router1.sockets['2.2.2.2'] = Mock()
        router1.sockets['3.3.3.3'] = Mock()


        message = 'hello world'
        packet = BBBPacket('2.2.2.2', '1.1.1.1', BBBPacketType.FLOOD, message, 0)
        router2.sign(packet)
        router1.keys['2.2.2.2'] = router2.packet_key.publickey()
        router1.handle_flood(packet, ('2.2.2.2', 9999))
        # Packet destined for router1. Shouldn't be flooded
        router1.sockets['2.2.2.2'].sendall.assert_not_called()
        router1.sockets['3.3.3.3'].sendall.assert_not_called()

    def test_handle_flood_flood(self):
        router1 = BasicRouter('1.1.1.1', test=True)
        router2 = BasicRouter('2.2.2.2', test=True)
        router1.neighbors.add('2.2.2.2')
        router1.neighbors.add('3.3.3.3')
        router1.sockets['2.2.2.2'] = Mock()
        router1.sockets['3.3.3.3'] = Mock()


        message = 'hello world'
        packet = BBBPacket('2.2.2.2', '3.3.3.3', BBBPacketType.FLOOD, message, 0)

        router2.sign(packet)
        router1.keys['2.2.2.2'] = router2.packet_key.publickey()
        router1.handle_flood(packet, ('2.2.2.2', 9999))
        # Packet should be sent to 3.3.3.3, but not 2.2.2.2
        router1.sockets['2.2.2.2'].sendall.assert_not_called()
        router1.sockets['3.3.3.3'].sendall.assert_called_with(packet.to_bytes())

    def test_handle_route_update(self):
        router1 = BasicRouter('1.1.1.1', test=True)
        router2 = BasicRouter('2.2.2.2', test=True)

        routes = ['3.3.3.3', '4.4.4.4', '5.5.5.5']

        route_packet = BBBPacket(
            '2.2.2.2',
            '1.1.1.1',
            BBBPacketType.ROUTEUPDATE,
            json.dumps(routes),
            0,
        )

        router2.sign(route_packet)

        router1.keys['2.2.2.2'] = router2.packet_key.publickey()
        router1.handle_routeupdate(route_packet)

        assert '2.2.2.2' in router1.neighbors
        for route in routes:
            assert route in router1.routes
            assert router1.routes[route] == '2.2.2.2'
        assert router1.routes['2.2.2.2'] == '2.2.2.2'
