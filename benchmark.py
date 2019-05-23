#!/usr/bin/env python

import json
import multiprocessing
import re
import socket
import subprocess
import sys
import time


fqdn = socket.getfqdn()
num_tests = 10
max_time = '360'

global_args = [
    '--threads=' + str(multiprocessing.cpu_count()),
    '--time=' + max_time
]

def parse_output(output, data):
    """ Parse sysbench text output and store the metric in a dict """
    for line in output.splitlines():
        if ":" not in line:
            continue
        name, value = line.split(":")
        if re.match(r'^sysbench', name):
            continue
        if value.strip() == "":
            continue
        data[name.strip()] = value.strip()
    return data

def run_test(name, **kwargs):
    """ Run a sysbench test with custom args """
    command = ["sysbench", name] + global_args

    for k,v in kwargs.iteritems():
        command.append('--%s=%s' % (k.replace('_', '-'),v))
    command.append('run')
    #print command
    return subprocess.check_output(command)

def main(args):
    data = {}

    # Memory
    memory_blocks = ['1K', '4K','16K', '64K', '128K', '1M', '4M', '8M', '16M', '64M']
    kwargs = {'memory_total_size': '100T', 'memory_access_mode': 'rnd'}
    name = 'memory'
    data[name] = {}
    for i in range(num_tests):
        kwargs['memory_block_size'] = memory_blocks[i]
        data[name][i] = {}
        output = run_test(name, **kwargs)
        time.sleep(1)
        #print output
        parse_output(output, data[name][i])

    # Output json
    with open('benchmark.js', 'w') as outfile:
        json.dump(data, outfile, indent=2)

if __name__ == "__main__":
    sys.exit(main(sys.argv))
