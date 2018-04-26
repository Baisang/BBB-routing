#!/usr/bin/env python3
import argparse
import json
import os
import signal
import subprocess
import sys
import tempfile
import time

from bigchaindb_driver.crypto import generate_keypair

dir = os.path.dirname(__file__)
build_dir = os.path.join(dir, '../build')

# These are names of some OCF desktops
# proper way to do this is to query using ldap
# For now just hard code them I guess, am lazy
ALL_HOSTS = ['acid', 'arsenic', 'asteroid', 'avalanche', 'bigbang', 'blackout',
            'blight', 'chaos', 'cyanide', 'cyclone', 'destruction']

docker_compose = '~/BBB-routing/venv/bin/docker-compose'
docker_compose_yml = '~/BBB-routing/docker-compose.yml'


# returns a dict nodes that maps hostname to pub/privkey pair
def generate_keypairs(hosts):
    nodes = {}
    for host in hosts:
        keypair = generate_keypair()
        nodes[host] = keypair
    return nodes


# generates config files for all machines in the build/ directory with name
# `.bigchaindb-$HOST`. does all of the keyring stuff too
def generate_config(nodes):
    template_path = os.path.join(dir, '../bigchaindb-config.template')
    if not os.path.exists(build_dir):
        os.makedirs(build_dir)
    all_pubkeys = [nodes[k].public_key for k in nodes]
    with open(template_path, 'r') as template:
        d = json.load(template)
    for host, keypair in nodes.items():
        ip_addr = subprocess.check_output(['host', '-t', 'A', host])
        ip_addr = ip_addr.split()[-1].decode('utf-8')
        d['keypair']['private'] = keypair.private_key
        d['keypair']['public'] = keypair.public_key
        d['database']['host'] = ip_addr
        d['keyring'] = [k for k in all_pubkeys if k != keypair.public_key]
        config_path = os.path.join(build_dir, '.bigchaindb-{}'.format(host))
        with open(config_path, 'w') as config:
            json.dump(d, config, indent=4, sort_keys=True)
    print('Generated config files for all hosts')


def run_parallel_command(hosts, cmd):
    with tempfile.NamedTemporaryFile(mode='w') as f:
        f.write('\n'.join(hosts) + '\n')
        f.flush()
        pssh_args = ['-h', f.name] + cmd.split()
        try:
            print('{}::{}'.format(subprocess.check_output(['parallel-ssh'] + pssh_args).decode('utf-8').strip(), cmd))
        except subprocess.CalledProcessError as e:
            print('{}::{}'.format(e.output.decode('utf-8').strip(), cmd))

def wakeup(hosts):
    for host in hosts:
        print(subprocess.check_output(['lab-wakeup', host]).decode('utf-8').strip())

def bootstrap(num_machines):
    if num_machines % 2 == 0:
        print('Need an odd number of machines')
        return
    hosts = ALL_HOSTS[:num_machines]
    nodes = generate_keypairs(hosts)
    generate_config(nodes)
    # Maybe do something with lab wakeup here...
    wakeup(hosts)
    # Sleep 5 seconds to allow machines to wake up
    time.sleep(5)
    run_parallel_command(hosts, 'git clone https://github.com/Baisang/BBB-routing.git')
    run_parallel_command(hosts, 'mkdir ~/BBB-routing/build/')
    run_parallel_command(hosts, 'virtualenv ~/BBB-routing/venv/ --python=python3')
    run_parallel_command(hosts, '~/BBB-routing/venv/bin/pip3 install -r ~/BBB-routing/requirements.txt')
    for host in hosts:
        config_path = os.path.join(build_dir, '.bigchaindb-{}'.format(host))
        print(subprocess.check_output(
            ['scp', config_path, '{}:~/BBB-routing/build/.bigchaindb'.format(host)],
        ))

    # Start mongod service
    run_parallel_command(
        hosts,
        '{} -f {} up -d mdb'.format(docker_compose, docker_compose_yml),
    )

    # Sleep like 120 seconds to allow mongod to start up
    time.sleep(120)

    # If multiple nodes, establish primary/replica
    if num_machines >= 3:
        primary = hosts[:1]
        replicas = hosts[1:]
        replicas = [subprocess.check_output(['host', '-t', 'A', h]).split()[-1].decode('utf-8') for h in replicas]
        replica_args = ' '.join(['{}:27017'.format(ip) for ip in replicas])
        # Start bigchaindb on primary
        run_parallel_command(
                primary,
                '{} -f {} up -d bdb'.format(docker_compose, docker_compose_yml),
        )
        # Add replicas on primary
        run_parallel_command(
                primary, 
                '{} -f {} run bdb add-replicas {}'.format(docker_compose, docker_compose_yml, replica_args),
        )

    # Sleep like 30 seconds to let this process work out
    time.sleep(30)
    # Start bigchaindb on hosts
    run_parallel_command(
        hosts,
        '{} -f {} up -d bdb'.format(docker_compose, docker_compose_yml),
    )


def cleanup(hosts):
    run_parallel_command(
        hosts,
        '{} -f {} stop mdb'.format(docker_compose, docker_compose_yml),
    )
    run_parallel_command(
        hosts,
        '{} -f {} stop bdb'.format(docker_compose, docker_compose_yml),
    )
    run_parallel_command(
        hosts,
        '{} -vsf {} rm bdb'.format(docker_compose, docker_compose_yml),
    )
    run_parallel_command(
        hosts,
        '{} -vsf {} rm mdb'.format(docker_compose, docker_compose_yml),
    )
    run_parallel_command(
        hosts,
        'rm -rf ~/BBB-routing',
    )


def up(args):
    def handler(signum, frame):
        print('Cleaning up...')
        cleanup(ALL_HOSTS[:num_machines]) 
        print('Cleaned up all hosts, exiting...')
        sys.exit()

    num_machines = args.num_machines
    if num_machines % 2 == 0:
        print('Error, need an odd number of machines')
        return -1
    bootstrap(num_machines)
    signal.signal(signal.SIGINT, handler)
    print('Bootstrap successful, press CTRL+C to cleanup')
    while True:
        time.sleep(100)


def down(args):
    # TODO: do we need to lab wakeup??
    cleanup(ALL_HOSTS)
    print('Cleaned up all hosts')


def main(argv=None):
    parser = argparse.ArgumentParser(
        description='Utility to bootstrap and teardown a small bigchaindb cluster at the OCF. \
                Upon running the program, selected machines will be woken up and start running \
                bigchaindb. Exiting the script with CTRL+C will teardown the cluster. If the \
                program exits without tearing down, the cluster can be torn down by running the \
                program again with the `stop` command.',
    )

    subparsers = parser.add_subparsers(dest='command', help='command to run')
    subparsers.required = True

    parser_up = subparsers.add_parser(
        'up',
        help='bring up a cluster on a specified number of machines',
    )
    parser_up.add_argument(
        'num_machines',
        type=int,
        help='the number of machines in the cluster, must be odd',
    )
    parser_up.set_defaults(func=up)

    parser_down = subparsers.add_parser(
        'down',
        help='tear down a cluster by running teardown on all desktops',
    )
    parser_down.set_defaults(func=down)

    args = parser.parse_args(argv)
    return args.func(args)
    

if __name__ == '__main__':
    sys.exit(main())
