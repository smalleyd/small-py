from typing import Any
from datetime import datetime
from ..elastic.dao import BaseDAO
from elasticsearch import Elasticsearch
from ..models.mcp import Mcp, McpSearchRequest, Tool

class McpDAO(BaseDAO[Mcp, McpSearchRequest]):
    def __init__(self, es: Elasticsearch):
        super().__init__(es, "mcp", Mcp, {
            "properties":{
                "id": {"type": "keyword"},
                "name": {"type": "text", "fields": {"keyword": {"type": "keyword", "normalizer":"lowercase"}}},
                "slug": {"type": "keyword", "normalizer":"lowercase"},
                "description": {"type": "text"},
                "tools": {"properties":{
                    "method": {"type": "keyword"},
                    "name": {"type": "text"},
                    "description": {"type": "text"},
                    "url": {"type": "keyword", "normalizer":"lowercase"},
                    "headers": {"type": "flattened"},
                    "body_template": {"type": "text"},
                    "input_schema": {"type": "flattened"},
                    "response_transform": {"type": "text"},
                    "timeout_ms": {"type": "long"}
                }},
                "authentication": {"properties":{
                    "type": {"type": "keyword"},
                    "header": {"type": "keyword", "normalizer": "lowercase"},
                    "url": {"type": "keyword", "normalizer": "lowercase"}
                }},
                "oauth": {"properties":{
                    "authorization_url": {"type": "keyword", "normalizer": "lowercase"},
                    "token_url": {"type": "keyword", "normalizer": "lowercase"},
                    "client_id": {"type": "keyword", "normalizer": "lowercase"},
                    "client_secret": {"type": "keyword", "normalizer": "lowercase"},
                    "scopes": {"type": "keyword", "normalizer": "lowercase"},
                    "extra_params": {"type": "flattened"}
                }},
                "creator": {"properties":{
                    "id": {"type": "keyword"},
                    "name": {"type": "text", "fields": {"keyword": {"type": "keyword", "ignore_above": 256, "normalizer":"lowercase"}}}
                }},
                "created_at": {"type": "date"},
                "updated_at": {"type": "date"},
                "archived_at": {"type": "date"}
            }
        })

        self.filter_has_oauth = {"exists": {"field": "oauth"}}
        self.filter_has_archived_at = {"exists": {"field": "archived_at"}}
        self.filter_has_authentication = {"exists": {"field": "authentication"}}

    def archive(self, id: str):
        now = datetime.now()
        super().set(id, "archived_at", now, now)

    def get_by_slug(self, value: str) -> Mcp:
        return self.get_by_query({"term": {"slug": value}})

    def has_slug(self, value: str) -> bool:
        return 0 < self._count({"term": {"slug": value}})

    def set_tools(self, id: str, values: list[Tool]):
        v = [i.model_dump(mode="json") for i in values]
        super().set(id, "tools", v)

    def before_save(self, id: str, value: dict[str, Any], exists: bool) -> dict[str, Any]:
        if "archived_at" in value: del value["archived_at"] # Should only be set by the archive method. DLS on 6/16/2026.

        return value

    def _build_query(self, f: McpSearchRequest) -> dict[str, Any]:
        must = []
        must_not = []
        if f.ids:
            must.append({"ids": {"values": f.ids}})
        if f.name:
            must.append({"match": {"name": { "query": f.name, "fuzziness": "AUTO" }}})
        if f.slug:
            must.append({"term": {"slug": f.slug}})
        if f.description:
            must.append({"match": {"description": { "query": f.description, "fuzziness": "AUTO" }}})
        if f.tools_name:
            must.append({"match": {"tools.name": { "query": f.tools_name, "fuzziness": "AUTO" }}})
        if f.tools_description:
            must.append({"match": {"tools.description": { "query": f.tools_description, "fuzziness": "AUTO" }}})
        if f.authentication_type:
            must.append({"term": {"authentication.type": f.authentication_type.value}})
        if f.authentication_header:
            must.append({"term": {"authentication.header": f.authentication_header}})
        if f.authentication_url:
            must.append({"term": {"authentication.url": f.authentication_url}})
        if f.has_authentication is not None:
            if f.has_authentication:
                must.append(self.filter_has_authentication)
            else:
                must_not.append(self.filter_has_authentication)
        if f.has_oauth is not None:
            (must if f.has_oauth else must_not).append(self.filter_has_oauth)
        if f.creator_id:
            must.append({"term": {"creator.id": f.creator_id}})
        if f.creator_name:
            must.append({"match": {"creator.name": {"query": f.creator_name, "fuzziness": "AUTO" }}})
        self.range_query(must, "created_at", f.created_at_from, f.created_at_to)
        self.range_query(must, "updated_at", f.updated_at_from, f.updated_at_to)
        self.range_query(must, "archived_at", f.archived_at_from, f.archived_at_to)

        if f.has_archived_at is not None:
            if f.has_archived_at:
                must.append(self.filter_has_archived_at)
            else:
                must_not.append(self.filter_has_archived_at)

        return {"bool": {"must": must, "must_not": must_not}}

    def _build_unique_key_query(self, value: dict[str, Any]) -> dict[str, Any] | None:
        if "slug" not in value:
            return None

        return {"term":{"slug": value["slug"]}}

    @property
    def unique_key(self) -> str:
        return "slug"
