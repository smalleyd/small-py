from datetime import datetime
from pydantic import ConfigDict
from ..elastic.dao import Entity, Filter

class Person(Entity):
    model_config = ConfigDict(extra="forbid")

    email: str
    first_name: str
    last_name: str
    name: str
    created_at: datetime | None = None
    updated_at: datetime | None = None
    archived_at: datetime | None = None
    auth_at: datetime | None = None

class PersonSearchRequest(Filter):
    model_config = ConfigDict(extra="forbid")

    ids: list[str] | None = None
    email: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    name: str | None = None
    created_at_from: datetime | None = None
    created_at_to: datetime | None = None
    updated_at_from: datetime | None = None
    updated_at_to: datetime | None = None
    archived_at_from: datetime | None = None
    archived_at_to: datetime | None = None
    has_archived_at: bool | None = None
    auth_at_from: datetime | None = None
    auth_at_to: datetime | None = None
    has_auth_at: bool | None = None
