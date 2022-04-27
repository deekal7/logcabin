#!/usr/bin/env xonsh
import argparse
import sys
sys.path.insert(0, './slooo')
from tests.logcabin.test_main import *

def parse_opt():
    parser = argparse.ArgumentParser()
    parser.add_argument("--iters", type=int, default=1, help="number of iterations")
    parser.add_argument("--workload", type=str, default="resources/workloads/workloada", help="workload path")
    parser.add_argument("--server-configs", type=str, default="server_config.json", help="server config path")
    parser.add_argument("--runtime", type=int, default=300, help="runtime")
    parser.add_argument("--exps", type=str, default="1", help="experiments to be ran saperated by commas(,)")
    parser.add_argument("--exp-type", type=str, default="leader", help="leader/follower/both")
    parser.add_argument("--ondisk", type=str, default="mem", help="in memory(mem) or on disk (disk)")
    parser.add_argument("--threads", type=int, default=250, help="no. of logical clients")
    parser.add_argument("--output-path", type=str, default="results", help="results output path")
    parser.add_argument("--cleanup", action='store_true', help="clean's up the servers")
    parser.add_argument("--fault-snooze", type=int, default=0, help="After how long from the start of sending reqs should the fault be injected")
    opt = parser.parse_args()
    return opt

def main(opt):
    for iter in range(1,opt.iters+1):
        exps = [exp.strip() for exp in opt.exps.split(",")]
        for exp in exps:
            DB = LogCabin(opt=opt,trial=iter,exp=exp)
            DB.run()
            sleep 30

if __name__ == "__main__":
    print("In main")
    opt = parse_opt()
    main(opt)