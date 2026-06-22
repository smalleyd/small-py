"""
    Represents the models and component to manage One Time Passwords (OTP) for authentication.
"""

import random, string
from typing import Annotated
from dataclasses import field
from pydantic import BaseModel, Field
from redis import ConnectionPool, Redis
from datetime import datetime, timedelta

def generate_token() -> str:
    return "".join(random.choices(string.ascii_uppercase)[0] for _ in range(6))

KEY = "otp"
max_failures = 5
expiration_minutes = 10
expiration = timedelta(minutes=expiration_minutes)

class Token(BaseModel):
    value: Annotated[str, Field(min_length=6, max_length=8)] = field(default_factory=generate_token)
    expires_at: datetime = field(default_factory=lambda: datetime.now() + expiration)
    failures: int = 0

class OtpDAO():
    def __init__(self, connection_pool: ConnectionPool, db: int = 0):
        self.db = db
        self.connection_pool = connection_pool

    def dbx(self) -> Redis:
        return Redis(connection_pool=self.connection_pool, db=self.db)

    def generate(self, email: str):
        o = Token()

        self.dbx().hsetex(KEY, email, o.model_dump_json(), ex=expiration)

        return o

    def get(self, email: str) -> Token | None:
        o = self.dbx().hget(KEY, email)
        return Token.model_validate_json(json_data=o) if o else None

    def ttl(self, email: str) -> int:
        return self.dbx().httl(KEY, email)[0]

    def check(self, email: str, value: str) -> bool:
        dbx = self.dbx()
        entry = dbx.hget(KEY, email)
        if not entry:
            return False

        token = Token.model_validate_json(json_data=entry)

        if token.value == value:
            dbx.hdel(KEY, email)
            return True

        token.failures = token.failures + 1
        if max_failures <= token.failures:
            dbx.hdel(KEY, email)
        else:
            dbx.hsetex(KEY, email, token.model_dump_json(), ex=timedelta(minutes=expiration_minutes - token.failures))

        return False