from datetime import datetime
from pydantic import BaseModel

class AccessToken(BaseModel):
  access_token: str
  token_type: str = "bearer"

class Person(BaseModel):
  id: str | None = None
  name: str | None = None
  email: str | None = None
  created_at: datetime | None = None
  updated_at: datetime | None = None

class PersonSearchRequest(BaseModel):
  ids: list[str] | None = None
  name: str | None = None
  email: str | None = None