import socket
import json
from os.path import join as path_join
from time import sleep
from base import (
    BBBPacket, BBBPacketType,
    ROUTER_PORT
)


TOPO_DIRECTORY = "topologies"
TOPO_UPDATE_PERIOD = 5

class MasterRouter(object):
    def __init__(self, topo_path="simple.json"):
        self.sockets = {}

        # Load the network topology from the json file
        self.topology = {}
        with open(path_join(TOPO_DIRECTORY, topo_path), 'r') as topo_file:
            self.topology = json.loads(topo_file.read())

        # while True:
        # for each host, send a BBBPacket with appropriate routes
        for host, routes in self.topology.items():
            print("attempting to connect to: {0}".format(host))
            endpoint = (host, ROUTER_PORT)
            try:
                host_socket = self.sockets[endpoint]
            except KeyError:
                host_socket = socket.socket()
                self.sockets[endpoint] = host_socket
                host_socket.connect(endpoint)
            route_packet = BBBPacket(
                socket.gethostbyname(socket.getfqdn()),
                host,
                BBBPacketType.ROUTEUPDATE,
                json.dumps(routes)
            )
            a = route_packet.to_bytes()
            b = BBBPacket.from_bytes(a)
            host_socket.sendall(a)
            # sleep(TOPO_UPDATE_PERIOD)

if __name__ == "__main__":
    MasterRouter()
