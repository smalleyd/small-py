from os import getenv
from datetime import datetime
from urllib.error import HTTPError
from typing import Any, Generic, TypeVar

from elasticsearch import (
    Elasticsearch,
    NotFoundError
)

E = TypeVar("E")
F = TypeVar("F")

class BaseDAO(Generic[E, F]):
    def __init__(self, es: Elasticsearch, index: str, clazz: type[E]):
        self.es = es
        self.index = index
        self.clazz = clazz

    @classmethod
    def connect(cls, envHost: str = "ES_HOST", envCreds: str = "ES_CREDS"):
        host = getenv(envHost, "localhost")
        creds = getenv(envCreds)
        if not creds:
            raise Exception(f"Missing {envCreds}")

        creds_ = creds.split(":", 2)
        if len(creds_) != 2:
            raise Exception(f"Invalid {envCreds}")

        crd = creds_[0], creds_[1]

        return Elasticsearch(
            f"https://{host}",
            basic_auth=crd,
            max_retries=5,
            retry_on_status=[409, 429, 500, 502, 503, 504])

    def ping(self) -> bool:
        return self.es.ping()

    def does_exist(self, id:str):
        if not self.exists(id):
            raise HTTPError(code=404, msg=f"Missing {id}", url="ES:exists", hdrs={}, fp=None)

    def exists(self, id:str) -> bool:
        return self.es.exists(index=self.index, id=id).body

    def get(self,
        id: str,
        *,
        includes: list[str] | None = None,
        excludes: list[str] | None = None,
        vectors: bool = False
    ) -> E:
        resp = self.es.get(index=self.index,
            id=id,
            source_exclude_vectors=vectors,
            source_excludes=excludes,
            source_includes=includes)
        o = resp.get("_source", None)

        return self.clazz(**o) if o else None

    def get_created_at(self, id:str) -> datetime | None:
        try:
            resp = self.es.get(index=self.index,
                id=id,
                source_includes=["created_at"])
            if not resp["found"]: return None
        except NotFoundError:
            return None

        return resp["_source"].get(self.field_created_at, None)

    def add(self, value: E) -> E:
        self.es.index(index=self.index, id=value.id, document=value.__dict__)

        return value

    def before_save(self, id:str, value: dict[str, Any], exists: bool) -> dict[str, Any]:
        return value

    def patch(self, id:str, value: dict[str, Any]):
        self.does_exist(id)

        if "id" in value: del value["id"]
        if self.field_created_at in value: del value[self.field_created_at]
        value[self.field_updated_at] = datetime.now()

        self.update(id, self.before_save(id, value, True))

    def refresh(self):
        self.es.indices.refresh(index=self.index)

    def remove(self, id:str) -> None:
        self.es.delete(index=self.index, id=id)

    def set(self, id:str, field:str, value:Any | None):
        self.does_exist(id)

        self.update(id, {field: value, self.field_updated_at: datetime.now()})

    def update(self, id:str, value: dict[str, Any]) -> None:
        self.es.update(index=self.index, id=id, doc=value)

    def upsert(self, value: E) -> E:
        """
        Indexes the supplied value to the components 'index' but sets the 'created_at' and 'updated_at' fields
        before saving.

        :param value:
        :return: the supplied value
        """
        v = value.__dict__
        now = datetime.now()
        v[self.field_updated_at] = now
        created_at = self.get_created_at(value.id)  # Do NOT update the created_at field if it already exists.
        exists = created_at is not None
        v[self.field_created_at] = created_at if exists else now

        self.es.index(index=self.index, id=value.id, document=self.before_save(value.id, v, exists))

        return self.clazz(**v)

    def count(self, filter: F) -> int:
        return self.es.count(index=self.index, query=self.build_query(filter)).body["count"]

    def search(self, filter: F) -> list[E]:
        hits = self.es.search(
            index=self.index,
            query=self.build_query(filter))["hits"]["hits"]
        if not hits:
            return []

        return [self.clazz(**hit["_source"]) for hit in hits]

    def build_query(self, filter: F) -> dict[str, Any]:
        return {"match_all": {}} if self.empty(filter) else self._build_query(filter)

    def _build_query(self, filter: F) -> dict[str, Any]:
        """Derived class must implement this method to handle its search request."""
        return {"match_all": {}}

    def empty(self, filter: F) -> bool:
        for v in filter.__dict__.values():
            if v:
                return False
        return True

    @property
    def field_created_at(self) -> str:
        """Derived class can optionally override."""
        return "created_at"

    @property
    def field_updated_at(self) -> str:
        """Derived class can optionally override."""
        return "updated_at"