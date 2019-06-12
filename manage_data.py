#!/usr/bin/env python

import argparse
import json
import os
import sys
from prettytable import PrettyTable

from sqlalchemy import Column, Float, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import func
from datetime import datetime

# db
class Resource(object):

    def update(self, attributes):
        for k, v in attributes.iteritems():
            setattr(self, k, v)

    @staticmethod
    def create(cls, data):
        new_data = dict()
        for k, v in data.iteritems():
            if k == 'id':
                continue
            if k in cls.__dict__:
                new_data[k] = v
        return cls(**new_data)

Base = declarative_base(cls=Resource)

class Cpu(Base):
    __tablename__ = 'cpu'
    id = Column(Integer, primary_key=True)
    max_prime = Column(Integer, index=True)
    threads = Column(Integer)
    events = Column(Integer, nullable=False)
    avg = Column(Float)
    type = Column(String(15))
    hostname = Column(String(255))
    created = Column(DateTime, default=datetime.now)

class Memory(Base):
    __tablename__ = 'memory'
    id = Column(Integer, primary_key=True)
    block_size = Column(String(63), nullable=False, index=True)
    events = Column(Integer, nullable=False)
    threads = Column(Integer)
    avg = Column(Float)
    type = Column(String(15))
    hostname = Column(String(255))
    created = Column(DateTime, default=datetime.now)

# Parser
actions = ['parse', 'show-memory', 'show-cpu']
arguments = dict()
arguments['parse'] = list()
arguments['parse'].append({'name': 'path', 'metavar': 'path'})
arguments['parse'].append({'name': 'type', 'metavar': 'type'})
arguments['show-memory'] = list()
arguments['show-memory'].append({'name': 'type', 'metavar': 'type'})
arguments['show-cpu'] = list()
arguments['show-cpu'].append({'name': 'type', 'metavar': 'type'})

parser = argparse.ArgumentParser()
subparser = parser.add_subparsers(title='action')

for action in actions:
    a = subparser.add_parser(action)
    a.set_defaults(action=action)
    if not action in arguments:
        continue
    for arg in arguments[action]:
        name = arg['name']
        del arg['name']
        a.add_argument(name, **arg)

options = parser.parse_args()

# SQLalchemy
db = './metric.db'
engine = create_engine('sqlite:///%s' % db)
Base.metadata.bind = engine
DBSession = sessionmaker()
session = DBSession()
Base.metadata.create_all(engine)

def action_show_memory():
    blocks = session.query(Memory.block_size).distinct().order_by(Memory.block_size).all()
    t = PrettyTable(['Max prime', 'Avg', 'Events'])
    t.align = 'l'
    for block_size in blocks:
        size = block_size[0]
        avg = session.query(func.avg(Memory.avg).label('average')).filter(Memory.type==options.type, Memory.block_size==size).all()
        events = session.query(func.avg(Memory.events).label('average')).filter(Memory.type==options.type, Memory.block_size==size).all()

        t.add_row([size, str("%.2f" % round(float(avg[0][0]),2)), str("%.2f" % round(float(events[0][0]),2))])
    #t.sortby = 'Block size'
    print t

def action_show_cpu():
    primes = session.query(Cpu.max_prime).distinct().order_by(Cpu.max_prime).all()
    t = PrettyTable(['Max prime', 'Avg', 'Events'])
    t.align = 'r'
    for max_prime in primes:
        prime = max_prime[0]
        avg = session.query(func.avg(Cpu.avg).label('average')).filter(Cpu.type==options.type, Cpu.max_prime==prime).all()
        events = session.query(func.avg(Cpu.events).label('average')).filter(Cpu.type==options.type, Cpu.max_prime==prime).all()

        t.add_row([prime, str("%.2f" % round(float(avg[0][0]),2)), str("%.2f" % round(float(events[0][0]),2))])
    #t.sortby = 'Block size'
    print t

def action_parse():
    module = __import__(__name__)
    files = get_files(options.path)
    for f in files:
        hostname, data_type = get_meta(f)
        with open(f) as json_file:
            data = json.load(json_file)
            for type,hosts in data.iteritems():
                print 'parse %s...' % type
                dbclass_ = getattr(module, type.capitalize())
                for key,values in hosts.iteritems():
                    if type == 'memory':
                        metric_data = get_metric(values, ['block_size'])
                    elif type == 'cpu':
                        metric_data = get_metric(values, ['max_prime'])
                    else:
                        metric_data = get_metric(values)

                    metric = dbclass_.create(dbclass_, metric_data)
                    session.add(metric)
                    session.commit()

def get_metric(values, extra_metric = []):
    default_metrics = ['events', 'avg', 'type', 'threads', 'hostname']
    metrics = extra_metric + default_metrics
    metric_data = dict()
    for metric in metrics:
        if metric == 'events':
            value = int(values['total number of events'])
        elif metric == 'avg':
            value = float(values['avg'])
        elif metric == 'threads':
            value = float(values['Number of threads'])
        elif metric == 'type':
            value = options.type # FIXME
        elif metric == 'max_prime':
            value = int(values['Prime numbers limit'])
        elif metric == 'block_size':
            value = values['block size']
        else:
            value = values[metric]
        metric_data[metric] = value
    return metric_data

def get_meta(path):
    hostname = os.path.basename(os.path.dirname(path))
    data_type = options.type
    return hostname,data_type

def get_files(path):
    files = list()
    # r=root, d=directories, f = files
    for r, d, f in os.walk(path):
        for file in f:
            if '.js' in file:
                files.append(os.path.join(r, file))
    return files


# Run local function with the same name as the action (Note: - => _)
action = locals().get('action_' + options.action.replace('-', '_'))
if not action:
    print("Function action_%s not implemented" % options.action)
    sys.exit(1)
action()
