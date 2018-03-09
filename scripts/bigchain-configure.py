#!/usr/bin/env python3
import argparse
import json
import os
import subprocess
import sys

from bigchaindb_driver.crypto import generate_keypair

dir = os.path.dirname(__file__)
build_dir = os.path.join(dir, '../build')
config_path = os.path.join(build_dir, '.bigchaindb')

def generate_config(args):
    keypair = generate_keypair()
    template_path = os.path.join(dir, '../bigchaindb-config.template')
    # Get the IP address for the default interface
    # For OCF machines, this will be the first IP address returned.
    ip_addr = subprocess.check_output(['hostname', '--all-ip-addresses'])
    ip_addr = ip_addr.split()[0].decode('utf-8')
    with open(template_path, 'r') as template:
        d = json.load(template)
        d['keypair']['private'] = keypair.private_key
        d['keypair']['public'] = keypair.public_key
        d['database']['host'] = ip_addr

    if not os.path.exists(build_dir):
        os.makedirs(build_dir)
    with open(config_path, 'w') as config:
        json.dump(d, config, indent=4, sort_keys=True)
    print('Successfully generated config file .bigchaindb')


def add_keyring(args):
    public_key = args.public_key

    with open(config_path, 'r') as config:
        d = json.load(config)

    # Ensure that public_key to add is not already the node's public_key
    if public_key == d['keypair']['public']:
        print('public_key is the node\'s public key, cannot add to keyring')
        return 1
    # Ensure that the public_key to add is not already in the keyring
    if public_key in d['keyring']:
        print('public_key already in keyring')
        return 1

    d['keyring'].append(public_key)

    with open(config_path, 'w') as config:
        json.dump(d, config, indent=4, sort_keys=True)
    print('Successfully added public_key to keyring')


def main(argv=None):
    parser = argparse.ArgumentParser(
        description='Utility to generate and update configuration files for \
        bigchaindb',
    )

    subparsers = parser.add_subparsers(dest='command', help='command to run')
    subparsers.required = True

    parser_generate = subparsers.add_parser(
        'generate',
        help='generate a public/private keypair and .bigchaindb configuration',
    )
    parser_generate.set_defaults(func=generate_config)

    parser_add = subparsers.add_parser(
        'add',
        help='add the public key of a node to the keyring',
    )
    parser_add.add_argument(
        'public_key',
        help='the public key of the node',
    )
    parser_add.set_defaults(func=add_keyring)

    args = parser.parse_args(argv)
    return args.func(args)

if __name__ == '__main__':
    sys.exit(main())


