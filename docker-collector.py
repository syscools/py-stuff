from pymongo import MongoClient
import pymongo
from pprint import pprint as pp
import time

key_names = (
    ('name','containerName'),
    ('created','containerCreated'),
    ('ports','containerPorts'),
    ('state','containerState'),
    ('externalId','containerId'),
    ('imageUuid','containerImage'))

def adjust_key_names(d):
    if not isinstance(d,dict):
        raise TypeError
    for native_name,req_name in key_names:
        d[req_name] = d.pop(native_name)

mongocli = MongoClient(host = 'mopbz171199.fr.dst.ibm.com')
DB = mongocli.get_database('docker-beta_cloud_dst_ibm_com:8080')
last_collection_date = DB.last_ts.find().next()
ts = last_collection_date['value']

def get_collection_dates():
    collection_dates = DB.collection_dates.find({},{'checkdate':1})
    return collection_dates

def get_environments():
    environments = DB.environments.find({'ts':ts},{'name':1,'description':1})
    return environments

def get_stacks():
    stacks = DB.stacks.find({'ts':ts},{'name':1,'description':1})
    return stacks

def get_services():
    services = DB.services.find({'ts':ts},{'name':1,'state':1})
    return services

def get_containers():
    #containers = DB.containers.find()
    containers = DB.containers.find({'ts':ts})
    return containers

def get_dockerhosts():
    dockerhosts = DB.dockerhosts.find_one()['values']
    return dockerhosts

if __name__ == '__main__':
    for container in get_containers():
        adjust_key_names(container)
        #pp(container)
        name = container['containerName']
        state = container['containerState']
        host = container['containerHost']
        if state == 'running':
            #print name,state,host
            a,b = host.split('/')
            x = eval(b)
            print name,a,x[0]
        print "*" * 20
