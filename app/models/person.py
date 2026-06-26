from enum import Enum
from . import patterns
from typing import Annotated
from datetime import datetime
from pydantic import ConfigDict, Field
from ..elastic.dao import Entity, Filter

class Source(Enum):
    EMAIL = "Email"
    GITHUB = "GitHub"
    GOOGLE = "Google"

class Type(Enum):
    USER = "user"
    ADMIN = "admin"

class Person(Entity):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    email: Annotated[str, Field(pattern=patterns.EMAIL)]
    first_name: Annotated[str, Field(min_length=1, max_length=50)]
    last_name: Annotated[str, Field(min_length=1, max_length=50)]
    name: Annotated[str, Field(min_length=1, max_length=105)]
    type: Type = Type.USER
    source: Source = Source.EMAIL
    created_at: datetime | None = None
    updated_at: datetime | None = None
    archived_at: datetime | None = None
    auth_at: datetime | None = None

class PersonSearchRequest(Filter):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    ids: list[str] | None = None
    email: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    name: str | None = None
    type: Type | None = None
    source: Source | None = None
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
