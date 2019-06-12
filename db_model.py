from sqlalchemy import Column, Float, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

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
