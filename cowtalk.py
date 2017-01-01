import sys
import socket
import requests
from requests.auth import HTTPDigestAuth
from pprint import pprint as pp
from pprint import pformat as pf
import logging
import json
import six
from treelib import Node,Tree
import datetime
import time
from pymongo import MongoClient

logger = logging.getLogger(__file__)
logger.setLevel(logging.DEBUG)
h1 = logging.FileHandler('/tmp/cow.log','w')
h2 = logging.StreamHandler()
logger.addHandler(h1)
#logger.addHandler(h2)

'''
myResponse = requests.get(url,auth=HTTPDigestAuth(raw_input("username: "),
                          raw_input("Password: ")), verify=True)
'''

def REST_get(url):
    try:
        val = requests.get(url)
        logger.debug(url)
        return val.status_code,val.json()
    except requests.ConnectionError:
        print "REST error 503"
        return 503,{}
    except ValueError:
        print "REST ValueError"
        return val.status_code,{}

URL = 'http://{ipaddr}:{port}/v1/projects'

env_fields = \
    ('id',
     'name',
     'description')

stack_fields = \
    ('id',
     'description',
     'accountId',
     'name',
     'state',
     'created',
     'dockerCompose',
     'createdTS')

service_fields = \
    ('id',
     'accountId',
     'environmentId',
     'name',
     'state',
     'created',
     'createdTS')

container_fields = \
    ('name',
     'externalId',
     'state',
     'created',
     'imageUuid',
     'ports',
     'id',
     'accountId')

host_fields = \
    ('hostname',
     'accounId')

def copy_fields(thedict,fields = None):
    if fields is None:
        return thedict
    else:
        return {field:thedict.get(field,'@') for field in fields} 

def talk_to_the_cow(tcpendpoint):
    t0 = time.time()
    endpointstr = '%s:%d' % tcpendpoint
    rancher_index = mongocli.get_database('rancher_index')
    rancher_index.endpoints.update_one({'_id':1}, {"$addToSet":{"values":{"$each":[endpointstr]}}},True)

    db_name = tcpendpoint[0].replace('.','_') + ':' + str(tcpendpoint[1])
    DB = mongocli.get_database(db_name)    
    # this unix epoch timestamp is what binds together the 
    # collection_dates,environments,stacks,services and 
    # containers collections
    ts = time.time()
    ts_human = datetime.datetime.now().isoformat()
    DB.collection_dates.insert({'checkdate':ts_human,'ts':ts, 'by':socket.gethostname()})
    TREE = Tree()
    data = {'checkdate':ts_human,'ts':ts}
    env_node = Node(tag = 'Environments',identifier = 'Environments',data = data)
    TREE.add_node(env_node)

    ########################################
    # get the environment(s) of this Rancher
    ########################################
    url = URL.format(ipaddr = tcpendpoint[0],port = tcpendpoint[1])
    retcode,environments = REST_get(url)
    for environment in environments['data']:
        print "E",
        env_data = copy_fields(environment,env_fields)
        #env_data = copy_fields(environment)
        env_data['ts'] = ts
        env_node = Node(tag = environment['name'],identifier = environment['id'], data = env_data)
        DB.environments.insert(env_data)
        TREE.add_node(env_node,parent = 'Environments')

        ####################################
        # get the stack(s) of an environment
        ####################################
        env_url = url + '/' + environment['id'] + '/environments'
        retcode,stacks = REST_get(env_url)
        for stack in stacks['data']:
            print "S",
            stack_data = copy_fields(stack,stack_fields)
            stack_data['ts'] = ts
            DB.stacks.insert(stack_data)
            stack_node = Node(tag = stack['name'], identifier = stack['id'],data = stack_data)
            TREE.add_node(stack_node,parent = environment['id'])

            ###############################
            # get the service(s) of a stack
            ###############################
            service_url = stack['links']['services']
            retcode,services = REST_get(service_url)
            for service in services['data']:
                print "Z",
                service_data = copy_fields(service, service_fields)
                service_data['ts'] = ts
                DB.services.insert(service_data)
                service_node = Node(tag = service['name'],identifier = service['id'], data = service_data)
                TREE.add_node(service_node,parent = stack['id'])

                ###################################
                # get the container(s) of a service 
                ###################################
                instance_url = service['links']['instances'] 
                retcode,containers = REST_get(instance_url)
                for container in containers['data']:
                    print "C",
                    p = container['ports']
                    ports = ','.join(p) if isinstance(p,list) and p else ''
                    con_data = copy_fields(container,container_fields)
                    con_data['ts'] = ts
                    
                    DB.containers.insert(con_data)
                    con_node = Node(tag = container['name'], identifier = container['id'],data = con_data)
                    TREE.add_node(con_node,parent = service['id'])
                    
                    ################################
                    # get the host(s) of a container
                    ################################
                    hosts_url = container['links']['hosts']                 
                    retcode,hosts = REST_get(hosts_url)
                    hostname = '?'
                    for host in hosts['data']:
                        print "H",
                        ipaddrs = set(endpoint['ipAddress'] for endpoint in host['publicEndpoints'])
                        host_data = copy_fields(host,host_fields)
                        host_data['ts'] = ts
                        host_data['checkdate'] = ts_human
                        host_data['ipaddrs'] = ipaddrs
                        hostname = "%s/%s" % (host['hostname'],list(ipaddrs))
                        #hostname = host['hostname']
                        host_node = Node(tag = hostname, identifier = host['id'],data = host_data)
                        try:
                            TREE.add_node(host_node,parent = container['id'])
                            DB.dockerhosts.update_one({'ts':ts,'checkdate':ts_human}, {"$addToSet":{"values":{"$each":[hostname]}}},True)
                        except:
                            pass
                   

                    #------------------------------------------
                    # update the container data with new fields
                    #------------------------------------------
                    attachinfo = {}
                    attachinfo['containerHost'] = hostname 
                    attachinfo['containerDouId'] = environment['description']
                    ret = DB.containers.update({'id':container['id'],'ts':ts},{"$set":attachinfo})
        print ""                
    DB.last_ts.update({'_id':1},{'value':ts,'checkdate':ts_human},True)
    t1 = time.time()
    duration = t1 - t0
    DB.collection_dates.update_one({'ts':ts},{"$set":{"duration":duration}})
    try:
        ###########################
        # write to mongodb database
        # redis will follow later for asynchronous communication between processes
        ##########################################################################
        print "\n"
        TREE.show()
    except UnicodeEncodeError,e:
        print "%s" % e

class Shepherd(object):
    def __init__(self,tcpendpoint):
        ipaddr,port = tcpendpoint
        self.ipaddr = ipaddr
        self.port = port
    
    def get_environments(self):
        return []

    def get_stacks_from_environment(self,env):
        return []

    def get_services_from_stack(self,stack):
        return []

    def get_containers_from_service(self,service):
        return []

mongocli = MongoClient(host = 'mopbz171199.cloud.dst.ibm.com',port = 27017)

if __name__ == '__main__':
    if len(sys.argv) == 1:
        print("usage: %s 192.168.2.1:8080" % sys.argv[0])
        sys.exit(1)
    
    print '''Legends:
E = Environment
S = Stack
Z = Service
C = Container
H = Host'''
    print "-" * 10
    arg = sys.argv[1].split(':')
    tcpendpoint = (arg[0],int(arg[1]))
    talk_to_the_cow(tcpendpoint)
