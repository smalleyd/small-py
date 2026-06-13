import sys
from .elastic.dao import BaseDAO
from elasticsearch import Elasticsearch

es: Elasticsearch
if sys.argv[-1] == 'dev':
  from .elastic import tester
  es = tester.client
else:
  es = BaseDAO.connect()
