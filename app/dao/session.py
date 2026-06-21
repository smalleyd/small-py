from typing import Any
from .person import mappings
from ..elastic.dao import BaseDAO
from elasticsearch import Elasticsearch
from ..models.session import Session, SessionSearchRequest

class SessionDAO(BaseDAO[Session, SessionSearchRequest]):
    def __init__(self, es: Elasticsearch):
        super().__init__(
            es,
            index="session_",
            clazz=Session,
            mappings={"properties":{
                "id": {"type": "keyword"},
                "person": mappings,
                "duration": {"type": "integer"},
                "expires_at": {"type": "date"},
                "created_at": {"type": "date"},
                "updated_at": {"type": "date"}
            }})

        self.filter_has_duration = {"exists": {"field": "duration"}}
        self.filter_has_expires_at = {"exists": {"field": "expires_at"}}

    def _build_query(self, f: SessionSearchRequest) -> dict[str, Any]:
        must = []
        must_not = []
        if f.ids:
            must.append({"ids": {"values": f.ids}})
        if f.person_id:
            must.append({"term": {"person.id": f.person_id}})
        if f.email:
            must.append({"term": {"person.email": f.email}})
        if f.name:
            must.append({"match": {"person.name": { "query": f.name, "fuzziness": "AUTO" }}})
        if f.type:
            must.append({"term": {"person.type": f.type.value}})
        if f.duration:
            must.append({"term": {"duration": f.duration}})

        self.range_query(must, "duration", f.duration_from, f.duration_to)
        self.range_query(must, "expires_at", f.expires_at_from, f.expires_at_to)
        self.range_query(must, "created_at", f.created_at_from, f.created_at_to)
        self.range_query(must, "updated_at", f.updated_at_from, f.updated_at_to)

        if f.has_duration is not None:
            if f.has_duration:
                must.append(self.filter_has_duration)
            else:
                must_not.append(self.filter_has_duration)

        if f.has_expires_at is not None:
            if f.has_expires_at:
                must.append(self.filter_has_expires_at)
            else:
                must_not.append(self.filter_has_expires_at)

        return {"bool": {"must": must, "must_not": must_not}}