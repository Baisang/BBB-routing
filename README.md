# BBB-routing
🅱🅱🅱-routing - Berkeley Byzantine Block routing, a simulation of Radia Perlman's
[Network layer protocols with Byzantine robustness (NPBR)](https://dspace.mit.edu/handle/1721.1/14403)
scheme with a blockchain database (currently [BigchainDB](https://github.com/bigchaindb/bigchaindb))
serving as a trustless public key database.

This project is under active development and details are likely to change radically in the near future.

## Basic Structure
The simulation runs on top of the application layer using the python socket interface. Each node is a separate computer that has
a simulated router running, which may be benign or malicious, and also an instance of BigchainDB functioning as a distributed
public key database. A master node distributes network topologies to all of the nodes for simulation purposes.

Each router uses separate threads to emulate the time-sharing approach described in the NPBR paper. Separate threads are used to
disseminate routing information to neighbors, sending data to neighbors, and receiving data from neighbors. Locks are used to
guarantee synchronization amongst threads. For this reason, throughput is understandably slow but our intention was not to maximize
throughput in our simulation, rather to demonstrate that it is feasible to implement. Routers keep internal state (sequence
numbers, sockets between neighbors, etc.) and query BigchainDB for public keys when necessary.

Packets are defined using Python objects and serialized to JSON when needed. Using protobuf or another serialization format was
considered, but not implemented due to time constraints.

## Single Node Setup
We support installations on Debian Stretch, but this should all work on other Debian based systems as well.

0. Dependencies. We require the following dependencies to be installed:
  - `virtualenv`
  - `python3`
  - `libffi-dev`
  - `libssl-dev`
  - `python3-pip`
  - `docker` - [installation instructions](https://docs.docker.com/install/linux/docker-ce/debian/)
  - `libcrack2-dev`

All should be install-able from `apt` or through other instructions linked.

1. Setup your `virtualenv` like so:

```
virtualenv venv --python=python3
. venv/bin/activate
```

This will set up and activate your `virtualenv`

2. Install python packages from `requirements.txt`:

```
pip3 install -r requirements.txt
```

3. Generate an example BigchainDB configuration file

```
./scripts/bigchain-configure.py generate
```

This will create a file `.bigchaindb` inside of the `build/` directory. This
file is used for configuration by BigchainDB.

4. Start MongoDB

```
docker-compose up -d mdb
```

The `-d` flag means deatched, so it'll run in the background. If you want to
see the status of your containers, use the `docker images` command.

5. Start BigchainDB

```
docker-compose up bdb
```

Feel free to use the `-d` flag here too, if you want.

6. Start a router

```
python -m sim.basic_router <IP address to listen on>
```

We also have a sample malicious router provided that drops all data (FLOOD) packets, `sim.byzantine_routers`.

7. Start the master
We use a master node to send network topology to each router. The master node is in `sim/master.py`. It takes in a JSON config
file that expresses the topology of the network. Some examples are in `sim/topologies`.

8. Cleanup

```
docker-compose stop mdb
docker-compose stop bdb
```

You may also want to remove the stopped docker containers as well if you want to reset the BigchainDB database.

## Multi-node Setup
We used desktops at the [Open Computing Facility (OCF)](https://ocf.berkeley.edu) for multi-node setup. We wrote a script to
bootstrap multiple desktops in parallel. This script has many OCF-isms, but should be useful for writing your own script to
bootstrap multiple machines as well. The script is in `scripts/bigchain-ocf-setup.py` and essentially follows the same commands
as the single node setup, but on multiple machines.

After setting up BigchainDB on all machines, you can then log into each machine and run routers, have a master distribute the
network topology, and then try sending messages from each router to another. A basic message can be sent with the command
`flood <IP of dest> <count>`. Routers will print out each packet they receive and verify.
