from enum import Enum
from datetime import datetime
from typing import Annotated, Any
from ..elastic.dao import Entity, Filter
from pydantic import BaseModel, ConfigDict, Field

class AuthType(Enum):
    ApiKey = 'ApiKey'
    Basic = 'Basic'
    Bearer = 'Bearer'

class Method(Enum):
    GET = 'GET'
    POST = 'POST'
    PUT = 'PUT'
    PATCH = 'PATCH'
    DELETE = 'DELETE'
    HEAD = 'HEAD'
    OPTIONS = 'OPTIONS'
    TRACE = 'TRACE'

class Authentication(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    type: AuthType
    header: Annotated[str | None, Field(min_length=1, max_length=100)] = None
    url: Annotated[str, Field(pattern="^(http|https)://[\\w\\.\\-/!:#?=&%,@]+$")]

class Tool(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    method: Method
    name: Annotated[str, Field(min_length=1, max_length=200)]
    description: Annotated[str, Field(min_length=1, max_length=10000)]
    url: Annotated[str, Field(pattern="^(http|https)://[\\w\\.\\-/!:#?=&%,@]+$")]
    headers: Annotated[dict[str, str], Field(min_length=1, max_length=20)]
    body_template: Annotated[str | None, Field(min_length=1, max_length=50000)] = None
    input_schema: Annotated[dict[str, Any], Field(min_length=1, max_length=100)]
    response_transform: Annotated[str, Field(min_length=1, max_length=10000)]
    timeout_ms: Annotated[int, Field(ge=0, le=20000)]

class Mcp(Entity):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    name: Annotated[str, Field(min_length=1, max_length=500)]
    slug: Annotated[str, Field(min_length=1, max_length=60, pattern="^[\\w\\-]+$")]
    description: Annotated[str | None, Field(min_length=1, max_length=5000)] = None
    tools: list[Tool]
    authentication: Authentication | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    archived_at: datetime | None = None

class McpSearchRequest(Filter):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    ids: list[str] | None = None
    name: str | None = None
    slug: str | None = None
    description: str | None = None
    tools_name: str | None = None
    tools_description: str | None = None
    authentication_type: AuthType | None = None
    authentication_header: str | None = None
    authentication_url: str | None = None
    has_authentication: bool | None = None
    created_at_from: datetime | None = None
    created_at_to: datetime | None = None
    updated_at_from: datetime | None = None
    updated_at_to: datetime | None = None
    archived_at_from: datetime | None = None
    archived_at_to: datetime | None = None
    has_archived_at: bool | None = None
