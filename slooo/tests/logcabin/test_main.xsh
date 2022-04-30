#!/usr/bin/env xonsh
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

import collections
from multiprocessing import Process
import os
import random
import subprocess
import time
import re
import logging

from utils.quorum import Quorum
from utils.common_utils import *
from faults.fault_inject import fault_inject


def sh(command, bg=False, **kwargs):
    """Execute a local command."""

    kwargs['shell'] = True
    if bg:
        return subprocess.Popen(command, **kwargs)
    else:
        subprocess.check_call(command, **kwargs)


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
                    continue
                m = re.search('Now leader for term (\d+)', line)
                if m is not None:
                    b['leader'] = server_id
                    b['term'] = int(m.group(1))
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
            time.sleep(5)


class LogCabin(Quorum):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        results_path = os.path.join(self.output_path, "logcabin_{}_{}_{}_{}_results".format(
            self.exp_type, "swapon" if self.swap else "swapoff", self.ondisk, self.threads))
        try:
            os.rmdir(results_path)
        except:
            pass
        os.mkdir(results_path)
        self.results_txt = os.path.join(
            results_path, "{}_{}.txt".format(self.exp, self.trial))
        self.processes = collections.defaultdict()
        self.smokehosts = hosts = [
            ('127.0.0.1:5255', '127.0.0.1:5255', 1),
            ('127.0.0.1:5256', '127.0.0.1:5256', 2),
            ('127.0.0.1:5257', '127.0.0.1:5257', 3),
        ]
        self.client_command = 'build/Examples/OriginalBenchmark'
        self.server_command = 'build/LogCabin'
        self.num_servers = 3

        self.server_ids = range(1, self.num_servers + 1)
        self.cluster = "--cluster=%s" % ','.join([h[0] for h in
                                                  self.smokehosts[:self.num_servers]])

        sh('rm -rf smoketeststorage/')
        sh('rm -rf storage/')
        sh('rm -f debug/*')
        sh('mkdir -p debug')

    def server_setup(self):
        print('Initializing first server\'s log')
        command = ('%s --config logcabin-%d.conf' %
                   (self.server_command, 1))
        p = subprocess.Popen('%s --bootstrap --config logcabin-%d.conf' %
                             (self.server_command, self.server_ids[0]),
                             shell=True,
                             stderr=open('debug/bootstrap', 'w'),
                             stdout=subprocess.DEVNULL)

        time.sleep(10)

        for server_id in self.server_ids:
            host = self.smokehosts[server_id - 1]
            command = ('%s --config logcabin-%d.conf' %
                       (self.server_command, server_id))
            print('Starting %s on %s' % (command, host[0]))

            p = subprocess.Popen(command,
                                 shell=True,
                                 stderr=open('debug/%d' % server_id, 'w'),
                                 stdout=subprocess.DEVNULL)

            print('Server id: %d' % (server_id))
            print('Process id: %d' % (p.pid))
            self.processes[server_id] = p
            time.sleep(10)
        time.sleep(10)

    def start_db(self):
        print('Growing cluster')
        rcfg = subprocess.Popen('build/Examples/Reconfigure %s set %s' %
                                (self.cluster,
                                 ' '.join([h[0] for h in self.smokehosts[:self.num_servers]])),
                                shell=True,
                                stderr=subprocess.DEVNULL,
                                stdout=subprocess.DEVNULL)

        time.sleep(10)
        for idx, cfg in enumerate(self.server_configs):
            pid = self.processes[int(cfg['name'])].pid + 1
            print('Binding process %d' % pid)
            command = f"taskset -cp {cfg['cpu']} {pid}"
            sleep 5
            try:
                sh(command)
            except:
                print("Failed to bind process %d to cpu %d" % (pid, cfg['cpu']))
                pass

    def db_init(self):
        roles = await_stable_leader(self.server_ids)
        primary = roles['leader']
        secondary = ""
        for k, v in self.processes.items():
            if k != primary:
                secondary = k
                break

        print('Server %d is the leader ' % (primary))
        print('Server %d is the follower ' % (secondary))

        fault_replica = ""
        if self.exp_type == "follower":
            self.fault_pids = str(self.processes[secondary].pid + 1)
            fault_replica = str(secondary)
        elif self.exp_type == "leader":
            self.fault_pids = str(self.processes[primary].pid + 1)
            fault_replica = str(primary)

        for cfg in self.server_configs:
            if cfg['name'] == fault_replica:
                self.fault_server_config = cfg
        print(self.fault_pids)
        time.sleep(10)

    def benchmark_load(self):
        pass

    def benchmark_run(self):
        print(self.single_run)
        if not self.single_run:
            writers = 1
            while writers <= 50:
                writers_command = '--threads %s' % writers
                client = subprocess.Popen('%s %s %s' % (self.client_command, self.cluster, writers_command),
                                        shell=True,
                                        stdout=open('outputs/follower-mem-cont', 'a+'),
                                        stderr=open('debug/client', 'w'))
                writers += 2
                time.sleep(40)
        else:
            print("In single run")
            writers = 27
            writers_command = '--threads %s' % writers
            print_command = '--printLatency %s' % 1
            client = subprocess.Popen('%s %s %s %s' % (self.client_command, self.cluster, writers_command, print_command),
                                        shell=True,
                                        stdout=open('mem_contention_leader/1', 'a+'),
                                        stderr=open('debug/client', 'w'))
        time.sleep(40)

    def db_cleanup(self):
        try:
            sh('killall LogCabin')
            sh('killall Reconfigure')
            sh('killall OriginalBenchmark')
        except:
            pass

    def run(self):
        self.db_cleanup()
        self.server_setup()
        self.start_db()

        self.db_init()
        self.benchmark_load()

        self.fault_process = Process(target=fault_inject, args=(
            self.exp, self.fault_server_config, self.fault_pids, self.fault_snooze, ))
        self.fault_process.start()
        sleep 30

        self.benchmark_run()
        self.fault_process.join()
        self.db_cleanup()
