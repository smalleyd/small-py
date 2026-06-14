import sys
from .elastic.dao import BaseDAO
from elasticsearch import Elasticsearch

es: Elasticsearch
arg = sys.argv[-1]
if arg == 'dev' or arg.find('pytest') >= 0:
  from .elastic import tester
  es = tester.client
else:
  es = BaseDAO.connect()
