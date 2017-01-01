import redis
import os

CACHE_URL = os.getenv('CACHE_URL')
CACHE_PASS = os.getenv('CACHE_PASS')

CACHE = redis.Redis(host = CACHE_URL,password = CACHE_PASS)
channel = CACHE.pubsub()
channel.subscribe('conrefreshnotif')
for event in channel.listen():
    print event
