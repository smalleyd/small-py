from fastapi import Depends
from typing import Annotated
from urllib.error import HTTPError
from .models.session import Session
from .dao.startup import session_dao
from fastapi.security import APIKeyHeader
from .models.common import HEADER_API_KEY

auth_key = APIKeyHeader(name=HEADER_API_KEY)

async def auth(key: Annotated[str, Depends(auth_key)]) -> Session:
    return session_dao.check(key)

async def auth_admin(session: Annotated[Session, Depends(auth)]) -> Session:
    if not session.admin():
        raise HTTPError(code=403, msg="Not authorized", url="security::auth_admin", hdrs={}, fp=None)

    return session