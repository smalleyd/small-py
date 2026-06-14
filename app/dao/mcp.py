from typing import Any
from datetime import datetime
from ..elastic.dao import BaseDAO
from elasticsearch import Elasticsearch
from ..models.mcp import Mcp, McpSearchRequest

class McpDAO(BaseDAO[Mcp, McpSearchRequest]):
    def __init__(self, es: Elasticsearch):
        super().__init__(es, "mcp", Mcp, {
            "properties":{
                "id": {"type": "keyword"},
                "name": {"type": "text", "fields": {"keyword": {"type": "keyword", "normalizer":"lowercase"}}},
                "slug": {"type": "keyword", "normalizer":"lowercase"},
                "description": {"type": "text"},
                "api_key": {"type": "keyword"},
                "tools":{"properties":{
                    "name": {"type": "text"},
                    "description": {"type": "text"},
                    "input_schema": {"type": "flattened"},
                    "execution_config": {"properties":{
                        "url": {"type": "keyword", "normalizer":"lowercase"},
                        "method": {"type": "keyword"},
                        "headers": {"type": "flattened"},
                        "body_template": {"type": "text"},
                        "authentication": {"type": "keyword"}
                    }},
                    "response_transform": {"type": "text"},
                    "timeout_ms": {"type": "long"}
                }},
                "created_at": {"type": "date"},
                "updated_at": {"type": "date"},
                "archived_at": {"type": "date"}
            }
        })

        self.filter_has_archived_at = {"exists": {"field": "archived_at"}}

    def archive(self, id: str):
        now = datetime.now()
        super().set(id, "archived_at", now, now)

    def _build_query(self, f: McpSearchRequest) -> dict[str, Any]:
        o = []
        nots = []
        if f.ids:
            o.append({"ids": {"values": f.ids}})
        if f.name:
            o.append({"match": {"name": { "query": f.name, "fuzziness": "AUTO" }}})
        if f.slug:
            o.append({"term": {"slug": f.slug}})
        if f.description:
            o.append({"match": {"description": { "query": f.description, "fuzziness": "AUTO" }}})
        if f.tools_name:
            o.append({"match": {"tools.name": { "query": f.tools_name, "fuzziness": "AUTO" }}})
        if f.tools_description:
            o.append({"match": {"tools.description": { "query": f.tools_description, "fuzziness": "AUTO" }}})
        self.range_query(o, "created_at", f.created_at_from, f.created_at_to)
        self.range_query(o, "updated_at", f.updated_at_from, f.updated_at_to)
        self.range_query(o, "archived_at", f.archived_at_from, f.archived_at_to)

        if f.has_archived_at is not None:
            if f.has_archived_at:
                o.append(self.filter_has_archived_at)
            else:
                nots.append(self.filter_has_archived_at)

        return {"bool": {"must": o, "must_not": nots}}
