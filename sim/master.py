import socket
import json
from os.path import join as path_join
from time import sleep
from sim.base import (
    BBBPacket, BBBPacketType,
    ROUTER_PORT
)


TOPO_DIRECTORY = "sim/topologies"
TOPO_UPDATE_PERIOD = 30

class Master(object):
    """Master Node.
    Responsible for parsing topology information from a JSON file and sending
    corresponding packets to configure routers.
    """
    def __init__(self, topo_path="simple.json"):
        """Constructor
        @topo_path      name of the topology file to parse
        """
        self.sockets = {}
        seq_num = 0

        # Load the network topology from the json file
        self.topology = {}
        with open(path_join(TOPO_DIRECTORY, topo_path), 'r') as topo_file:
            self.topology = json.loads(topo_file.read())

        while True:
            for host, config in self.topology.items():
                # get corresponding socket for host
                print("attempting to connect to: {0}".format(host))
                endpoint = (host, ROUTER_PORT)
                try:
                    host_socket = self.sockets[endpoint]
                except KeyError:
                    # create and store a new socket if necessary
                    host_socket = socket.socket()
                    self.sockets[endpoint] = host_socket
                    host_socket.connect(endpoint)

                # create configuration packet and send it to the host
                config_packet = BBBPacket(
                    src=host_socket.getsockname()[0],
                    dst=host,
                    type=BBBPacketType.MASTERCONFIG,
                    payload=json.dumps(config),
                    seq=seq_num,
                )
                host_socket.sendall(config_packet.to_bytes())
                seq_num += 1
            sleep(TOPO_UPDATE_PERIOD)

if __name__ == "__main__":
    Master(topo_path = 'basic-byzantine.json')
