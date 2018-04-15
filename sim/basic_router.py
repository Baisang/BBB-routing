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
    """Basic Router Class
    Multithreaded server, structured as follows:
        Main Thread:
            Implements a basic cli by taking in user input
        ROUTEUPDATE Thread:
            Periodically sends local routing information to neighboring nodes
        LISTEN Thread:
            Listens/Accepts new connections, dispatches a client thread to
            handle any new sockets
        Client Thread:
            Created for every open socket, listens to the socket for data
            Dispatches read data to the proper handler
    """
    def __init__(self, ip_address):
        # Call parent's init
        super().__init__(ip_address)

        # Start LISTEN and ROUTEUPDATE thread
        threading.Thread(target=self.accept_connections).start()
        threading.Thread(target=self.update_neighbors).start()

        # Task main thread with handling CLI
        while True:
            cli_input = input()
            self.handle_cli(cli_input)


    def handle_cli(self, cli_input):
        """Tokenizes and calls proper handler for any recognized cli commands
        @cli_input      str parsed from user input
        """
        cli_input_tokens = cli_input.split()
        try:
            # Send command, format: send <ip> <cnt>
            # Simply sends <cnt> packets to <ip> from this router
            if cli_input_tokens[0] == "send":
                address, count = cli_input_tokens[1:]
                threading.Thread(target=self.send_hello(address, count)).start()
            else:
                raise Exception()
        except Exception as e:
            print(e)
            print("unrecognized command")

    def update_neighbors(self):
        """Periodically sends out routing information to neighbors.
        Implements Split Horizon to avoid Count-to-Infinity problems.
        """
        while True:
            # Calculate a dictionary where each key is the ip of a neighbor
            # and the value is a list of all the destinations we should display
            # format: {neighbor_ip: [dst_ip]}
            route_updates = {
                n: [d for d in self.routes if self.routes[d] != n]
                for n in self.neighbors
            }

            # Iterate through calculated updates
            for neighbor, routes in route_updates.items():
                if routes:
                    # Get old socket for the neighbors_ip if it exists
                    try:
                        neighbor_socket = self.sockets[neighbor]
                    except KeyError:
                        # If it does not exist, make a new one, store it in
                        # the list of open sockets and dispatch a client thread
                        neighbor_endpoint = (neighbor, ROUTER_PORT)
                        neighbor_socket = socket.socket()
                        neighbor_socket.connect(neighbor_endpoint)
                        self.sockets[neighbor] = neighbor_socket
                        threading.Thread(
                            target=self.handle_client,
                            args=(neighbor_socket, neighbor_endpoint)
                        ).start()

                    # Create and send appropriate route packet for neighbor
                    route_packet = BBBPacket(
                        src=self.ip_address,
                        dst=neighbor,
                        type=BBBPacketType.ROUTEUPDATE,
                        payload=json.dumps(routes),
                        seq=0,
                        signature=""
                    )
                    neighbor_socket.sendall(route_packet.to_bytes())
            time.sleep(10)


    def accept_connections(self):
        """Listens for any incoming connections and attempts to accept them.
        Dispatches a Client thread for each accepted connection.
        """
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
        """
        if DEBUG:
            return True


    def handle_masterconfig(self, packet):
        """Handles MASTERCONFIG packets
        A masterconfig packet causes a router to add hosts, update routes,
        and add neighbors.
        """
        config = json.loads(packet.payload)
        for host in config["hosts"]:
            self.routes[host] = None
        self.hosts = config["hosts"]
        self.neighbors = self.neighbors.union(config["neighbors"])

    def handle_routeupdate(self, packet):
        """Handles ROUTEUPDATE packets
        A ROUTEUPDATE packet causes a router to update its routes and neighbors.
        """
        for dst in json.loads(packet.payload):
            self.routes[dst] = packet.src
            self.neighbors.add(packet.src)
        self.routes[packet.src] = packet.src

    def handle_payload(self, packet, address):
        """Handles PAYLOAD packets
        A payload packet is destined for this Router simply "accept it".
        Otherwise attempt to flood it out of all links except for the link that
        the packet came in on.
        """
        if packet.dst == self.ip_address or self.routes[packet.dst] == None:
            return

        for neighbor in self.neighbors:
            if neighbor != address[0]:
                neighbor_socket = self.sockets[neighbor]
                neighbor_socket.sendall(packet.to_bytes())

    def handle_packet(self, packet, address):
        """Main packet handler.
        Basically a switch statement that dispatches more specific handler
        based on the packet's BBBPacketType.
        @packet         BBBPacket instance to be handled
        @address        tuple of (ip, port)
        """
        if packet.type == BBBPacketType.MASTERCONFIG:
            self.handle_masterconfig(packet)
        elif packet.type == BBBPacketType.ROUTEUPDATE:
            self.handle_routeupdate(packet)
        elif packet.type == BBBPacketType.PAYLOAD:
            self.handle_payload(packet, address)
        else:
            raise Exception("Unsupported BBBPacketType")

    def handle_client(self, client_socket, address):
        """Listens on the client_socket at address.
        This function is expected to be run in a thread dispatched by the
        LISTEN thread.
        @client_socket      socket_instance produced by accept()
        @address            tuple of (ip, port)
        """
        while True:
            try:
                data = client_socket.recv(PACKET_LEN)
                if not data:
                    raise Exception('Client disconnected')

                packet = BBBPacket.from_bytes(data)
                if self.verify(packet):
                    self.handle_packet(packet, address)

                # self.print_diagnostics()

            except Exception as e:
                print(e)
                client_socket.close()
                return False

    def send_hello(self, address, count):
        """Function to simply send a packet with hello string as its payload.
        Invoked via CLI.
        """
        for i in range(int(count)):
            if address in self.routes:
                packet = BBBPacket(
                    src=self.ip_address,
                    dst=address,
                    type=BBBPacketType.PAYLOAD,
                    payload="hello-{0}".format(i),
                    seq=0,
                    signature=""
                )
                self.sockets[self.routes[address]].sendall(packet.to_bytes())
            time.sleep(10)

    def print_diagnostics(self):
        """Prints diagnostic information about this router.
        """
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
