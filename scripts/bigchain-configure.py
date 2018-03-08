#!/usr/bin/env python3
import argparse
import json
import os
import sys

from bigchaindb_driver.crypto import generate_keypair


def generate_config(args):
    keypair = generate_keypair()
    with open('../bigchaindb-config.template', 'r') as template:
        d = json.load(template)
        d['keypair']['private'] = keypair.private_key
        d['keypair']['public'] = keypair.public_key

    if not os.path.exists('../build'):
        os.makedirs('../build')
    with open('../build/.bigchaindb', 'w') as config:
        json.dump(d, config, indent=4, sort_keys=True)
    print('Successfully generated config file .bigchaindb')


def add_keyring(args):
    public_key = args.public_key

    with open('../build/.bigchaindb', 'r') as config:
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

    with open('../build/.bigchaindb', 'w') as config:
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


