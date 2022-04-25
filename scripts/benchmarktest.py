#!/usr/bin/env python
"""
This runs some basic tests against a LogCabin cluster.

Usage:
  smoketest.py [options]
  smoketest.py (-h | --help)

Options:
  -h --help            Show this help message and exit
  --binary=<cmd>       Server binary to execute [default: build/LogCabin]
  --client=<cmd>       Client binary to execute
                       [default: build/Examples/SmokeTest]
  --reconf=<opts>      Additional options to pass through to the Reconfigure
                       binary. [default: '']
  --servers=<num>      Number of servers [default: 5]
  --timeout=<seconds>  Number of seconds to wait for client to complete before
                       exiting with an error [default: 10]
"""

from __future__ import print_function, division

import collections
from common import sh, smokehosts
from docopt import docopt
import os
import random
import subprocess
import time
import re

processes = collections.defaultdict(list)


def same(seq):
    for x in seq:
        if x != seq[0]:
            return False
    return True


def await_stable_leader(server_ids, after_term=0):
    while True:
        server_beliefs = {}
        for server_id in server_ids:
            server_beliefs[server_id] = {'leader': None,
                                         'term': None,
                                         'wake': None}
            b = server_beliefs[server_id]
            for line in open('debug/%d' % server_id):
                m = re.search('All hail leader (\d+) for term (\d+)', line)
                if m is not None:
                    b['leader'] = int(m.group(1))
                    b['term'] = int(m.group(2))
                    print(b)
                    continue
                m = re.search('Now leader for term (\d+)', line)
                if m is not None:
                    b['leader'] = server_id
                    b['term'] = int(m.group(1))
                    print(b)
                    continue
                m = re.search('Running for election in term (\d+)', line)
                if m is not None:
                    b['wake'] = int(m.group(1))
        terms = [b['term'] for b in server_beliefs.values()]
        leaders = [b['leader'] for b in server_beliefs.values()]
        if same(terms) and terms[0] > after_term:
            assert same(leaders), server_beliefs
            return {'leader': leaders[0],
                    'term': terms[0]}
        else:
            time.sleep(.25)


def main():
    arguments = docopt(__doc__)
    client_command = arguments['--client']
    server_command = 'build/LogCabin'
    num_servers = int(arguments['--servers'])
    reconf_opts = ''
    if reconf_opts == "''":
        reconf_opts = ""
    timeout = int(arguments['--timeout'])

    server_ids = range(1, num_servers + 1)
    cluster = "--cluster=%s" % ','.join([h[0] for h in
                                        smokehosts[:num_servers]])

    sh('rm -rf smoketeststorage/')
    sh('rm -rf storage/')
    sh('rm -f debug/*')
    sh('mkdir -p debug')

    print('Initializing first server\'s log')
    command = ('%s --config logcabin-%d.conf' %
                   (server_command, 1))
    p = subprocess.Popen('%s --bootstrap --config logcabin-%d.conf' %
           (server_command, server_ids[0]),
           shell=True,
           stderr=open('debug/bootstrap', 'w'),
           stdout=subprocess.DEVNULL)
    processes[1] = p

    for server_id in server_ids:
        host = smokehosts[server_id - 1]
        command = ('%s --config logcabin-%d.conf' %
                   (server_command, server_id))
        print('Starting %s on %s' % (command, host[0]))

        p = subprocess.Popen('%s --bootstrap --config logcabin-%d.conf' %
               (server_command, server_ids[0]),
               shell=True,
               stderr=open('debug/%d' % server_id, 'w'),
               stdout=subprocess.DEVNULL)
        processes[server_id] = p

    print('Growing cluster')
    subprocess.Popen('build/Examples/Reconfigure %s %s set %s' %
       (cluster,
        reconf_opts,
        ' '.join([h[0] for h in smokehosts[:num_servers]])),
        shell=True,
        stdout=subprocess.DEVNULL)

    roles = await_stable_leader(server_ids)
    print('Server %d is the leader in term %d' % (roles['leader'], roles['term']))

    for k,v in processes.items():
        print('k = ', v.pid)

if __name__ == '__main__':
    main()