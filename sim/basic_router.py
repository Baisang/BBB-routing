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
        # self.accept_connections()

    def accept_connections(self):
        while True:
            client, address = self.socket.accept()
            client.settimeout(60)
            threading.Thread(
                target=self.handle_client,
                args=(client, address)
            ).start()
            time.sleep(10)

    def handle_client(self, client_socket, address):
        while True:
            try:
                data = client_socket.recv(PACKET_LEN)
                if data:
                    packet = BBBPacket.from_bytes(data)
                    if packet.type == BBBPacketType.ROUTEUPDATE:
                        self.routes.update(json.loads(packet.payload))
                    print(self.routes)
                else:
                    raise error('Client disconnected')
            except:
                client_socket.close()
                return False

if __name__ == "__main__":
    BasicRouter()
