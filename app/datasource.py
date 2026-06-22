import os
import sys
from .elastic.dao import BaseDAO
from redis import ConnectionPool
from elasticsearch import Elasticsearch

es: Elasticsearch
redis: ConnectionPool

arg = sys.argv[-1]
if arg == 'dev' or arg.find('pytest') >= 0:
    from .elastic import tester
    es = tester.client

    from .myredis import tester
    redis = tester.pool
else:
    es = BaseDAO.connect()

    redis_url = os.environ.get('REDIS_URL')
    if not redis_url:
        raise Exception('REDIS_URL not set')

    redis = ConnectionPool.from_url(redis_url)
