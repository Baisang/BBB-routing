from base import (
    BBBPacket, BBBPacketType, RouterBase,
    PACKET_LEN, ROUTER_PORT
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
                if neighbor == "42.42.42.42":
                    continue
                if routes:
                    try:
                        neighbor_socket = self.sockets[neighbor]
                    except KeyError:
                        neighbor_socket = socket.socket()
                        neighbor_socket.connect((neighbor, ROUTER_PORT))
                        self.sockets[neighbor] = neighbor_socket
                    route_packet = BBBPacket(
                        src=self.address,
                        dst=neighbor,
                        type=BBBPacketType.ROUTEUPDATE,
                        payload=json.dumps(routes),
                        seq=0,
                        signature=""
                    )
                    neighbor_socket.sendall(route_packet.to_bytes())
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

    def handle_masterconfig(self, packet):
        config = json.loads(packet.payload)
        for host in config["hosts"]:
            routes[host] = None
        self.hosts = config["hosts"]
        self.neighbors = set(config["neighbors"])

    def handle_routeupdate(self, packet):
        for dst in json.loads(packet.payload):
            self.routes[dst] = packet.src
            self.neighbors.add(packet.src)

    def handle_packet(self, packet):
        if packet.type == BBBPacketType.MASTERCONFIG:
            self.handle_master_packet(packet)
        elif packet.type == BBB.BBBPacketType.ROUTEUPDATE:
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
                self.handle_packet(packet)

                print("new packet from {0}".format(packet.src))
                pprint(self.routes, width=1)
                pprint(self.neighbors, width=1)
                print()

            except Exception as e:
                print(e)
                client_socket.close()
                return False

if __name__ == "__main__":
    if len(sys.argv) == 2:
        BasicRouter(sys.argv[1])
    else:
        print("please run python3 basic_router.py <local-IP>")
