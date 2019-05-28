#!/usr/bin/env python

import json
import multiprocessing
import re
import socket
import subprocess
import sys
import time
import argparse

fqdn = socket.getfqdn()
num_tests = 10
data = {}

# Parser
actions = ['memory', 'cpu']
parser = argparse.ArgumentParser()
subparser = parser.add_subparsers(title='action')

for action in actions:
    a = subparser.add_parser(action)
    a.set_defaults(action=action)
    a.add_argument('time', metavar='time')

options = parser.parse_args()

global_args = [
    '--threads=' + str(multiprocessing.cpu_count()),
    '--time=' + options.time
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

def run_test(name, global_args, **kwargs):
    """ Run a sysbench test with custom args """
    command = ["sysbench", name] + global_args

    for k,v in kwargs.iteritems():
        command.append('--%s=%s' % (k.replace('_', '-'),v))
    command.append('run')
    #print command
    return subprocess.check_output(command)

def action_io():
    pass

def action_cpu():
    max_prime = ['1000', '5000', '10000', '20000', '30000', '50000', '100000', '200000', '500000', '1000000' ]
    name = 'cpu'
    data[name] = {}
    for i in range(num_tests):
        kwargs = {'cpu_max_prime': max_prime[i]}
        data[name][i] = {}
        output = run_test(name, global_args, **kwargs)
        time.sleep(1)
        #print output
        parse_output(output, data[name][i])
        data[name][i]['hostname'] = fqdn
    write_file(name + '.js', data)

def action_memory():
    memory_blocks = ['1K', '4K','16K', '64K', '128K', '1M', '4M', '8M', '16M', '64M']
    kwargs = {'memory_total_size': '100T', 'memory_access_mode': 'rnd'}
    name = 'memory'
    data[name] = {}
    for i in range(num_tests):
        kwargs['memory_block_size'] = memory_blocks[i]
        data[name][i] = {}
        output = run_test(name, global_args, **kwargs)
        time.sleep(1)
        #print output
        parse_output(output, data[name][i])
        data[name][i]['hostname'] = fqdn
    write_file(name + '.js', data)

def write_file(file, data):
    # Output json
    with open(file, 'w') as outfile:
        json.dump(data, outfile, indent=2)

def main(args):
    args.pop(0)
    if len(args) == 0:
        print >>sys.stderr, "Need at max time input"
        return 1






# Run local function with the same name as the action (Note: - => _)
action = locals().get('action_' + options.action.replace('-', '_'))
if not action:
    print("Function action_%s not implemented" % options.action)
    sys.exit(1)
action()
