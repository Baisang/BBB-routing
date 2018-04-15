from base import (
    BBBPacket, BBBPacketType, RouterBase,
    PACKET_LEN, ROUTER_PORT, DEBUG
)
import socket
import threading
import time
import json
import sys
from pprint import pprint


class BasicRouter(RouterBase):
    def __init__(self, address):
        super().__init__(address)
        threading.Thread(
            target=self.accept_connections
        ).start()
        threading.Thread(
            target=self.update_neighbors
        ).start()

    def update_neighbors(self):
        while True:
            print("updating neighbors {0}".format(self.neighbors))
            route_updates = {
                n: [d for d in self.routes if self.routes[d] != n]
                for n in self.neighbors
            }
            pprint(route_updates, width=1)
            for neighbor, routes in route_updates.items():
                if routes:
                    try:
                        neighbor_socket = self.sockets[neighbor]
                    except KeyError:
                        neighbor_endpoint = (neighbor, ROUTER_PORT)
                        neighbor_socket = socket.socket()
                        print("trying to connect to {0}".format(neighbor))

                        neighbor_socket.connect(neighbor_endpoint)
                        self.sockets[neighbor] = neighbor_socket
                        threading.Thread(
                            target=self.handle_client,
                            args=(neighbor_socket, neighbor_endpoint)
                        ).start()
                    route_packet = BBBPacket(
                        src=self.address,
                        dst=neighbor,
                        type=BBBPacketType.ROUTEUPDATE,
                        payload=json.dumps(routes),
                        seq=0,
                        signature=""
                    )
                    neighbor_socket.sendall(route_packet.to_bytes())
                    print("sent to {0}".format(neighbor))
            time.sleep(10)


    def accept_connections(self):
        while True:
            client, address = self.socket.accept()
            client.settimeout(60)
            self.sockets[address[0]] = client
            threading.Thread(
                target=self.handle_client,
                args=(client, address)
            ).start()

    def verify(self, packet):
        """
        TODO: Fill out this function
        If DEBUG parameter is true, return true.

        Verify packet's validity.
        If using Asymmetric Key Crypto:
            - Master Key is assumed to be public and trusted. Can use this
            to verify MASTERCONFIG packets and get keys for other nodes.
            - For other packets, check to see if we have public key and verify
            packet using seq and signature.
            - Fail safe, in case we don't have a key

        If using blockchain:
            - I have no idea.  @baisang pls
        """
        if DEBUG:
            return True


    def handle_masterconfig(self, packet):
        """
        A masterconfig packets causes a router to update
        routes, keys, and neighbors to match packet config info
        """
        config = json.loads(packet.payload)
        print(config, type(config))
        for host in config["hosts"]:
            self.routes[host] = None
        self.hosts = config["hosts"]
        self.neighbors = self.neighbors.union(config["neighbors"])

    def handle_routeupdate(self, packet):
        for dst in json.loads(packet.payload):
            self.routes[dst] = packet.src
            self.neighbors.add(packet.src)

    def handle_packet(self, packet):
        if packet.type == BBBPacketType.MASTERCONFIG:
            self.handle_masterconfig(packet)
        elif packet.type == BBBPacketType.ROUTEUPDATE:
            self.handle_routeupdate(packet)
        else:
            raise Exception("Unsupported BBBPacketType")

    def handle_client(self, client_socket, address):
        while True:
            try:
                data = client_socket.recv(PACKET_LEN)
                if not data:
                    raise Exception('Client disconnected')

                packet = BBBPacket.from_bytes(data)
                print("new packet from {0}".format(packet.src))
                if self.verify(packet):
                    self.handle_packet(packet)

                self.print_diagnostics()

            except Exception as e:
                print(e)
                client_socket.close()
                return False

    def print_diagnostics(self):
        print("***Routes***")
        pprint(self.routes, width=1)
        print("***neighbors***")
        pprint(self.neighbors, width=1)
        print("***sockets***")
        pprint(self.sockets, width=1)
        print("***keys***")
        pprint(self.keys, width=1)
        print()

if __name__ == "__main__":
    if len(sys.argv) == 2:
        BasicRouter(sys.argv[1])
    else:
        print("please run python3 basic_router.py <local-IP>")
