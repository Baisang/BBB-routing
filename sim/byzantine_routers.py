from sim.basic_router import BasicRouter
import sys

class FaultyFloodingRouter(BasicRouter):
    """Router that does not flood
    Can send and receive packets but does not forward packets.
    """

    def handle_flood(self, packet, address):
        """Handles FLOOD packets
        If the packet is destined for this Router simply "accept it".
        Otherwise the packet is dropped (and not forwarded).
        """
        if packet.dst == self.ip_address or packet.dst in self.hosts:
            print(packet.payload)

if __name__ == "__main__":
    if len(sys.argv) == 2:
        BasicRouter(sys.argv[1])
    else:
        print("please run python3 -m sim.basic_router <local-IP>")
