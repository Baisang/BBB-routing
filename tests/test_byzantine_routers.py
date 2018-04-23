import sim

from sim.base import BBBPacket, BBBPacketType
from sim.basic_router import BasicRouter
from sim.byzantine_routers import FaultyFloodingRouter

import unittest
from unittest.mock import Mock

class TestByzantineRouter(unittest.TestCase):

    def test_handle_flood_byzantine(self):
        router1 = FaultyFloodingRouter('1.1.1.1', test=True)
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
        # Packet should be dropped
        router1.sockets['2.2.2.2'].sendall.assert_not_called()
        router1.sockets['3.3.3.3'].sendall.assert_not_called()
