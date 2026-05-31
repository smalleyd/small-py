from elasticsearch import Elasticsearch
from testcontainers.elasticsearch import ElasticSearchContainer

container = ElasticSearchContainer("docker.elastic.co/elasticsearch/elasticsearch:9.3.0", 9200, mem_limit="1G").start()
host = container.get_container_host_ip()
port = container.get_exposed_port(9200)
client = Elasticsearch(f"http://{host}:{port}")
