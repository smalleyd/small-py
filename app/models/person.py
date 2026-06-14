from enum import Enum
from datetime import datetime
from pydantic import BaseModel
from ..elastic.dao import Filter

class AccessToken(BaseModel):
  access_token: str
  token_type: str = "bearer"

class Role(Enum):
  ADMIN = "admin"
  USER = "user"

class Person(BaseModel):
  id: str | None = None
  name: str | None = None
  email: str | None = None
  role: Role | None = None
  tags: set[str] | None = None
  created_at: datetime | None = None
  updated_at: datetime | None = None

class PersonSearchRequest(Filter):
  ids: list[str] | None = None
  name: str | None = None
  email: str | None = None
  role: Role | None = None
  tags: list[str] | None = None
  created_at_from: datetime | None = None
  created_at_to: datetime | None = None