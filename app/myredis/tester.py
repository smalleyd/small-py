import atexit
from redis import ConnectionPool
from testcontainers.redis import RedisContainer

container = RedisContainer(image="redis:8.4").start()
container.get_client()
pool = ConnectionPool(
    host=container.get_container_host_ip(),
    port=container.get_exposed_port(container.port)
)

def on_exit():
    pool.close()
    container.stop()

atexit.register(on_exit)
