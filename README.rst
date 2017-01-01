Design Notes
============

Databases:
    * docker-beta_cloud_dst_ibm_com:8080  
    * rancher_index

Collections inside **rancher_index**:
    * endpoints

Collections inside docker-beta_cloud_dst_ibm_com:8080:
    * collection_dates
    * containers
    * dockerhosts
    * environments
    * last_ts
    * services
    * stacks

**last_ts** is a single key/value pair that has the **ts** timestamp of
the last collection date completed. This **ts** value is then used to
get the relevant latest collection data. The value is Unix epoch seconds.
Therefore, calculate accordingly from client side, to determine if too old.

To narrow the return fields, do it like this when you call find():

..  code-block:: python

    from pymongo import MongoClient
    from pprint import pprint as pp

    cli = MongoClient(host = 'mopbz171199.fr.dst.ibm.com')
    DB = cli.get_database('docker-beta_cloud_dst_ibm_com:8080')
    latest = DB.last_ts.find().next()

    filter1 = {'ts':latest['value']}
    filter2 = {}
    filter3 = {'ts':1470862817.261788}

    containers = DB.containers.find(filter1,
        {'name':1,'state':1,'containerHost':1})

    for container in containers:
        #pp(container)
        print container['name'],container['state'],container['containerHost']
        print "-" * 20

The first parameter of find() is a filter dictionary. If it is empty, it means
get all the documents (aka rows) from the collection (aka table). The second
parameter of find() is used to narrow the fields of interest. From the
snippet above, only shows interest to the fields: name, state and containerHost.

Filter meanings
    * filter1 = get latest containers data for this rancher host
    * filter2 = get all containers data for this rancher host
    * filter3 = get containers data for the specified timestamp

Test run url:
http://smartcast.boulder.ibm.com:81?session=8d5f36ab-7f4a-4130-aafe-688a7bd44a87
