from os import getenv
from datetime import datetime
from urllib.error import HTTPError
from pydantic import BaseModel, Field
from dataclasses import dataclass, field
from typing import Annotated, Any, Generic, TypeVar

from elastic_transport._response import ObjectApiResponse
from elasticsearch import (
    Elasticsearch,
    NotFoundError
)

class Filter(BaseModel):
    page: Annotated[int, Field(ge=1, le=100)] = 1
    size: Annotated[int, Field(ge=1, le=1000)] = 10
    sort: Annotated[list[str], Field(min_length=1, max_length=10)] = ["created_at:Desc"]
    scroll: Annotated[str | None, Field(min_length=1, max_length=1000)] = None

    def from_page(self) -> int:
        return (self.page - 1) * self.size

E = TypeVar("E", bound=BaseModel)
F = TypeVar("F", bound=Filter)

@dataclass
class Results(Generic[E]):
    total: int = 0
    scroll_id: str | None = None
    data: list[E] = field(default_factory=list)
    scores: dict[str, float] = field(default_factory=dict)

class BaseDAO(Generic[E, F]):
    def __init__(
        self,
        es: Elasticsearch,
        index: str,
        clazz: type[E],
        mappings: dict[str, Any] | None = None,
        num_of_shards: int = 1
    ):
        self.es = es
        self.index = index
        self.clazz = clazz

        if mappings is not None:
            indices = es.indices
            if not indices.exists(index=self.index).body:
                indices.create(index=self.index, mappings=mappings, settings={"number_of_shards": num_of_shards})
            else:
                indices.put_mapping(index=self.index, body=mappings)

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
                source_includes=[self.field_created_at])

            return resp["_source"].get(self.field_created_at, None) if resp["found"] else None
        except NotFoundError:
            return None

    def add(self, value: E) -> E:
        self.es.index(index=self.index, id=value.id, document=self.to_dict(value), refresh="wait_for")

        return value

    def before_save(self, id:str, value: dict[str, Any], exists: bool) -> dict[str, Any]:
        return value

    def load(self, values: list[dict[str, Any]]) -> list[dict[str, Any]]:
        body = []
        for v in values:
            body.append({"index": {"_index": self.index, "_id": v["id"] }})
            body.append(v)

        self.es.bulk(index=self.index, body=body)

        return values

    def patch(self, id:str, value: dict[str, Any]):
        self.does_exist(id)

        if "id" in value: del value["id"]
        if self.field_created_at in value: del value[self.field_created_at]
        value[self.field_updated_at] = datetime.now()

        self.update(id, self.before_save(id, value, True))

    def refresh(self):
        self.es.indices.refresh(index=self.index)

    def remove(self, id:str) -> None:
        self.es.delete(index=self.index, id=id, refresh="wait_for")

    def set(self, id:str, field:str, value:Any | None, updated_at: datetime | None = None):
        self.does_exist(id)
        if updated_at is None: updated_at = datetime.now()

        self.update(id, {field: value, self.field_updated_at: updated_at})

    def update(self, id:str, value: dict[str, Any]) -> None:
        self.es.update(index=self.index, id=id, doc=value, refresh="wait_for")

    def upsert(self, value: E) -> E:
        """
        Indexes the supplied value to the components 'index' but sets the 'created_at' and 'updated_at' fields
        before saving.

        :param value:
        :return: the supplied value
        """
        now = datetime.now()
        v = self.to_dict(value)
        v[self.field_updated_at] = now
        created_at = self.get_created_at(value.id)  # Do NOT update the created_at field if it already exists.
        exists = created_at is not None
        v[self.field_created_at] = created_at if exists else now

        self.es.index(index=self.index, id=value.id, document=self.before_save(value.id, v, exists), refresh="wait_for")

        return self.clazz(**v)

    def count(self, filter: F) -> int:
        return self.es.count(index=self.index, query=self.build_query(filter)).body["count"]

    def ids(self, query: dict[str, Any], size: int) -> list[str]:
        resp = self.es.search(index=self.index, query=query, size=size, from_=0, source=False)
        hits = resp["hits"]["hits"]

        return [hit["_id"] for hit in hits] if hits else []

    def _results(self, resp: ObjectApiResponse[Any]) -> Results[E]:
        hits_ = resp["hits"]
        hits = hits_["hits"]
        total = hits_["total"]["value"]
        if not hits:
            return Results[E](total=total)

        return Results(
            total=total,
            scroll_id=resp["_scroll_id"] if "_scroll_id" in resp else None,
            data=[self.clazz(**hit["_source"]) for hit in hits],
            scores={hit["_id"]: hit["_score"] for hit in hits}
        )

    def scroll(self, id: str, time: str = "30s") -> Results[E]:
        return self._results(self.es.scroll(scroll_id=id,scroll=time))

    def search(self,
        filter_: F,
        source_exclude_vectors: bool = True,
        source_excludes: list[str] | None = None,
        source_includes: list[str] | None = None
    ) -> Results[E]:
        return self._results(self.es.search(
            index=self.index,
            from_=filter_.from_page(),
            size=filter_.size,
            scroll=filter_.scroll,
            sort=filter_.sort,
            track_scores=True,
            track_total_hits=True,
            source_excludes=source_excludes,
            source_includes=source_includes,
            source_exclude_vectors=source_exclude_vectors,
            query=self.build_query(filter_)))

    def build_query(self, filter: F) -> dict[str, Any]:
        return {"match_all": {}} if self.empty(filter) else self._build_query(filter)

    def _build_query(self, filter: F) -> dict[str, Any]:
        """Derived class must implement this method to handle its search request."""
        return {"match_all": {}}

    @staticmethod
    def empty(filter_: F) -> bool:
        for k, v in filter_.__dict__.items():
            if k not in ["page", "size", "sort", "scroll"] and v is not None:
                return False
        return True

    @staticmethod
    def range_query(query: list[dict[str, Any]], field: str, from_: Any, to_: Any):
        if from_ or to_:
            q = {}
            if from_: q["gte"] = from_
            if to_: q["lte"] = to_
            query.append({"range": {field: q}})

    def total_size_in_bytes(self) -> int:
        return self.es.indices.stats(index=self.index, metric="store")["_all"]["total"]["store"]["total_data_set_size_in_bytes"]

    @property
    def field_created_at(self) -> str:
        """Derived class can optionally override."""
        return "created_at"

    @property
    def field_updated_at(self) -> str:
        """Derived class can optionally override."""
        return "updated_at"

    def to_dict(self, o) -> Any:
        """
        NOT needed as long as E is a BaseModel.

        if isinstance(o, Enum):
            return o.value
        if hasattr(o, "__dict__"):
            return {k: self.to_dict(v) for (k, v) in o.__dict__.items() }
        if isinstance(o, list) or isinstance(o, tuple) or isinstance(o, set):   # CanNOT use Sequence because that includes str.
            return [self.to_dict(v) for v in o]

        return o
        """
        return o.model_dump(mode="json")
