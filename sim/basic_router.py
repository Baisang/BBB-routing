from base import (
    BBBPacket, BBBPacketType, RouterBase,
    PACKET_LEN, ROUTER_PORT
)
import socket
import threading
import time
import json


class BasicRouter(RouterBase):
    def __init__(self, address=""):
        super().__init__(address)
        threading.Thread(
            target=self.accept_connections
        ).start()
        threading.Thread(
            target=self.update_neighbors
        ).start()

    def update_neighbors(self):
        while True:
            print("updating neighbors")
            route_updates = {
                n: [d for d in self.routes if self.routes[d] != n]
                for n in self.neighbors
            }
            for neighbor, routes in route_updates:
                if routes:
                    try:
                        neighbor_socket = self.sockets[neighbor]
                    except KeyError:
                        neighbor_socket = socket.socket()
                        neighbor_socket.connect((neighbor, ROUTER_PORT))
                        self.sockets[neighbor] = neighbor_socket
                    route_packet = BBBPacket(
                        src=neighbor_socket.getsockname()[0],
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

    def handle_client(self, client_socket, address):
        while True:
            try:
                data = client_socket.recv(PACKET_LEN)
                if not data:
                    raise Exception('Client disconnected')

                packet = BBBPacket.from_bytes(data)
                if packet.type == BBBPacketType.ROUTEUPDATE:
                    for dst in json.loads(packet.payload):
                        self.routes[dst] = packet.src
                    self.neighbors.add(packet.src)
                    print(self.routes)
                    print(self.neighbors)
            except Exception as e:
                print(e)
                client_socket.close()
                return False

if __name__ == "__main__":
    BasicRouter()
