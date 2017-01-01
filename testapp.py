import os
import redis
import time
import json
from pymongo import MongoClient
from pprint import pprint as pp

REDIS_URL = os.getenv("REDIS_URL")
REDIS_PASS = os.getenv("REDIS_PASS")

CACHE = redis.Redis(host = REDIS_URL,password = REDIS_PASS,db = 1)
cli = MongoClient(host = 'mopbz171199.fr.dst.ibm.com')
DB = cli.get_database('docker-beta_cloud_dst_ibm_com:8080')
latest = DB.last_ts.find().next()

filter1 = {'ts':latest['value']}
filter2 = {}
filter3 = {'ts':1470862817.261788}

#containers = DB.containers.find(filter1,{'name':1,'state':1,'containerHost':1})
containers = DB.containers.find(filter1)

for container in containers:
    #pp(container)
    #print container['name'],container['state'],container['containerHost']

    #if container['state'] == 'running':
    if True:
        # hostname,x = container['containerHost'].split('/')
        # ipaddrs = eval(x)  
        # print container['name'],hostname,ipaddrs[0]
        containerID = container['externalId']
        if containerID is not None:
            container_stats = 'stats:' + containerID
            cstat = CACHE.get(container_stats)
            if cstat is not None:
                l = len(cstat)
                x = json.loads(cstat)
                l = x['cpu_stats']['system_cpu_usage']
            else:
                l = "NONE"
            print containerID,container['containerHost'],container['name'],l
        else:
            print "CNONE"

