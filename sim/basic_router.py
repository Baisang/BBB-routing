from base import (
    BBBPacketType, BBBPacket, RouterBase,
    PACKET_LEN, ROUTER_PORT
)
import socket
import threading

class BasicRouter(RouterBase):
    def __init__(self, address=""):
        super().__init__(address)
        threading.Thread(
            target=self.accept_connections
        ).start()

    def accept_connections(self):
        while True:
            client, address = self.socket.accept()
            client.settimeout(60)
            threading.Thread(
                target=self.handle_client,
                args=(client, address)
            ).start()

    def handle_client(self, client_socket, address):
        while True:
            try:
                data = client_socket.recv(PACKET_LEN)
                print("received {0}".format(data))
                if data:
                    # Set the response to echo back the recieved data
                    response = data
                    client_socket.send(response)
                else:
                    raise error('Client disconnected')
            except:
                client_socket.close()
                return False

if __name__ == "__main__":
    BasicRouter()
