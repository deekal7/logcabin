#!/usr/bin/env python
# Copyright (c) 2012-2014 Stanford University
# Copyright (c) 2014-2015 Diego Ongaro
#
# Permission to use, copy, modify, and distribute this software for any
# purpose with or without fee is hereby granted, provided that the above
# copyright notice and this permission notice appear in all copies.
#
# THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR(S) DISCLAIM ALL WARRANTIES
# WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
# MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL AUTHORS BE LIABLE FOR
# ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
# WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
# ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
# OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.

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
from common import sh, captureSh, Sandbox, smokehosts
from docopt import docopt
import os
import random
import subprocess
import time
import re

servers = {}

def same(seq):
    for x in seq:
        if x != seq[0]:
            return False
    return True

def await_stable_leader(sandbox, server_ids, after_term=0):
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
            sandbox.checkFailures()

def main():
    arguments = docopt(__doc__)
    client_command = arguments['--client']
    server_command = arguments['--binary']
    num_servers = int(arguments['--servers'])
    reconf_opts = arguments['--reconf']
    if reconf_opts == "''":
        reconf_opts = ""
    timeout = int(arguments['--timeout'])

    server_ids = range(1, num_servers + 1)
    cluster = "--cluster=%s" % ','.join([h[0] for h in
                                        smokehosts[:num_servers]])
    alphabet = [chr(ord('a') + i) for i in range(26)]
    cluster_uuid = ''.join([random.choice(alphabet) for i in range(8)])
    with Sandbox() as sandbox:
        sh('rm -rf smoketeststorage/')
        sh('rm -rf storage/')
        sh('rm -f debug/*')
        sh('mkdir -p debug')

        for server_id in server_ids:
            host = smokehosts[server_id - 1]
            with open('logcabin-%d.conf' % server_id, 'w') as f:
                f.write('serverId = %d\n' % server_id)
                f.write('listenAddresses = %s\n' % host[0])
                f.write('clusterUUID = %s\n' % cluster_uuid)
                f.write('snapshotMinLogSize = 1024')
                f.write('\n\n')
                try:
                    f.write(open('smoketest.conf').read())
                except:
                    pass


        print('Initializing first server\'s log')
        server = sandbox.rsh(smokehosts[0][0],
                    '%s --bootstrap --config logcabin-%d.conf' %
                    (server_command, server_ids[0]),
                   stderr=open('debug/bootstrap', 'w'))
        print()

        servers[server_ids[0]] = server

        for server_id in server_ids:
            host = smokehosts[server_id - 1]
            command = ('%s --config logcabin-%d.conf' %
                       (server_command, server_id))
            print('Starting %s on %s' % (command, host[0]))
            server = sandbox.rsh(host[0], command, bg=True,
                        stderr=open('debug/%d' % server_id, 'w'))
            sandbox.checkFailures()
            servers[server_id] = server        

        print('Growing cluster')
        sh('build/Examples/Reconfigure %s %s set %s' %
           (cluster,
            reconf_opts,
            ' '.join([h[0] for h in smokehosts[:num_servers]])))
        
        old = await_stable_leader(sandbox, server_ids)
        print('Server %d is the leader in term %d' % (old['leader'], old['term']))

        for p in sandbox.processes:
            print(p.proc.name)

        print('Starting %s %s on localhost' % (client_command, cluster))
        rps = 5
        writers = 1
        while writers <= 30:
            rps_command = '--rps %s' % rps
            writers_command = '--threads %s' % writers
            client = sandbox.rsh('localhost', '%s %s %s' % (client_command, cluster, writers_command),
                                bg=True,
                                stderr=open('debug/client', 'w'))
            writers += 1

            start = time.time()
            while client.proc.returncode is None:
                sandbox.checkFailures()
                time.sleep(.1)
                if time.time() - start > timeout:
                    raise Exception('timeout exceeded')

if __name__ == '__main__':
    main()
