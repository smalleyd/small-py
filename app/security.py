from fastapi import Depends
from typing import Annotated
from .models.session import Session
from .dao.startup import session_dao
from fastapi.security import APIKeyHeader

auth_key = APIKeyHeader(name="X-Contextly-Key")

async def auth(key: Annotated[str, Depends(auth_key)]) -> Session:
    return session_dao.check(key)
