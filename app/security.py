from fastapi.security import APIKeyHeader

auth = APIKeyHeader(name="X-Contextly-Key")
