from typing import Any
from datetime import datetime
from ..elastic.dao import BaseDAO
from elasticsearch import Elasticsearch
from ..models.person import Person, PersonSearchRequest

mappings = {"properties":{
    "id": {"type": "keyword"},
    "email": {"type": "keyword", "normalizer": "lowercase"},
    "first_name": {"type": "text", "fields": {"keyword": {"type": "keyword", "normalizer": "lowercase"}}},
    "last_name": {"type": "text", "fields": {"keyword": {"type": "keyword", "normalizer": "lowercase"}}},
    "name": {"type": "text", "fields": {"keyword": {"type": "keyword", "normalizer": "lowercase"}}},
    "type": {"type": "keyword"},
    "source": {"type": "keyword"},
    "created_at": {"type": "date"},
    "updated_at": {"type": "date"},
    "archived_at": {"type": "date"},
    "auth_at": {"type": "date"}
}}

class PersonDAO(BaseDAO[Person, PersonSearchRequest]):
    def __init__(self, es: Elasticsearch):
        super().__init__(es,
            index="person_",
            clazz = Person,
            mappings=mappings)

        self.filter_has_archived_at = {"exists": {"field": "archived_at"}}
        self.filter_has_auth_at = {"exists": {"field": "auth_at"}}

    def archive(self, id: str):
        now = datetime.now()
        super().set(id, "archived_at", now, now)

    def auth(self, id: str):
        now = datetime.now()
        super().set(id, "auth_at", now, now)

    def before_save(self, id: str, value: dict[str, Any], exists: bool) -> dict[str, Any]:
        if "archived_at" in value: del value["archived_at"] # Should only be set by the 'archive' method. DLS on 6/16/2026.
        if "auth_at" in value: del value["auth_at"] # Should only be set by the 'auth' method. DLS on 6/16/2026.

        return value

    def _build_query(self, f: PersonSearchRequest) -> dict[str, Any]:
        must = []
        must_not = []
        if f.ids:
            must.append({"ids": {"values": f.ids}})
        if f.email:
            must.append({"term": {"email": f.email}})
        if f.first_name:
            must.append({"match": {"first_name": { "query": f.first_name, "fuzziness": "AUTO" }}})
        if f.last_name:
            must.append({"match": {"last_name": { "query": f.last_name, "fuzziness": "AUTO" }}})
        if f.name:
            must.append({"match": {"name": { "query": f.name, "fuzziness": "AUTO" }}})
        if f.type:
            must.append({"term": {"type": f.type.value}})
        if f.source:
            must.append({"term": {"source": f.source.value}})

        self.range_query(must, "created_at", f.created_at_from, f.created_at_to)
        self.range_query(must, "updated_at", f.updated_at_from, f.updated_at_to)
        self.range_query(must, "archived_at", f.archived_at_from, f.archived_at_to)
        self.range_query(must, "auth_at", f.auth_at_from, f.auth_at_to)

        if f.has_archived_at is not None:
            if f.has_archived_at:
                must.append(self.filter_has_archived_at)
            else:
                must_not.append(self.filter_has_archived_at)

        if f.has_auth_at is not None:
            if f.has_auth_at:
                must.append(self.filter_has_auth_at)
            else:
                must_not.append(self.filter_has_auth_at)

        return {"bool": {"must": must, "must_not": must_not}}

    def _build_unique_key_query(self, value: dict[str, Any]) -> dict[str, Any] | None:
        if "email" not in value:
            return None

        return {"term": {"email": value["email"]}}

    @property
    def unique_key(self):
        return "email"