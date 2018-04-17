# BBB-routing
🅱🅱🅱-routing - Berkeley Byzantine Block routing, a simulation of Radia Perlman's [Network layer protocols with Byzantine robustness (NPBR)](https://dspace.mit.edu/handle/1721.1/14403) scheme with a blockchain database (currently [BigchainDB](https://github.com/bigchaindb/bigchaindb)) serving as a trustless public key database.

This project is under active development and details are likely to change radically in the near future.

## Setup
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


6. Cleanup

```
docker-compose stop mdb
docker-compose stop bdb
```

Simple as that
