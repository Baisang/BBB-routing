import socket
import json

from base import ROUTER_PORT
from os.path import join as path_join


TOPO_DIRECTORY = "topologies"


class MasterRouter(object):
    def __init__(self, topo_path="simple.json"):
        self.socket = socket.socket()

        # Load the network topology from the json file
        self.topology = {}
        with open(path_join(TOPO_DIRECTORY, topo_path), 'r') as topo_file:
            self.topology = json.loads(topo_file.read())

        # for each host, send a BBBPacket with appropriate routes
        for host, routes in self.topology.items():
            self.socket.connect((host, ROUTER_PORT))
            route_packet = BBBPacket(
                BBBPacketType.ROUTEUPDATE,
                json.dumps(routes).encode()
            )
            self.socket.sendall(route_packet.to_bytes())

if __name__ == "__main__":
    MasterRouter()
