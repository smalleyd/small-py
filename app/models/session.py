from typing import Annotated
from pydantic import Field, ConfigDict
from ..elastic.dao import Entity, Filter
from datetime import datetime, timedelta
from ..models.person import Person, Type

UPDATE_DELTA = timedelta(seconds=5)

class Session(Entity):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    person: Person
    duration: Annotated[int | None, Field(ge=5, default=30)]    # Minutes
    expires_at: datetime | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    def can_update(self) -> bool:
        return self.updated_at < (datetime.now() - UPDATE_DELTA)

    def expired(self) -> bool:
        return (self.expires_at is not None) and (self.expires_at < datetime.now())

    def admin(self) -> bool: return self.person.admin()
    def user(self) -> bool: return self.person.user()

class SessionSearchRequest(Filter):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    ids: list[str] | None = None
    person_id: str | None = None
    email: str | None = None
    name: str | None = None
    type: Type | None = None
    duration: int | None = None
    duration_from: int | None = None
    duration_to: int | None = None
    has_duration: bool | None = None
    expires_at_from: datetime | None = None
    expires_at_to: datetime | None = None
    has_expires_at: bool | None = None
    created_at_from: datetime | None = None
    created_at_to: datetime | None = None
    updated_at_from: datetime | None = None
    updated_at_to: datetime | None = None
