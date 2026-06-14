from enum import Enum
from typing import Annotated
from datetime import datetime
# from dataclasses import dataclass
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

# @dataclass
class ExecutionConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    url: Annotated[str, Field(pattern="^(http|https)://[\\w\\.\\-/!:#?=&%,@]+$")]
    method: Method
    headers: dict[str, str]
    body_template: Annotated[str | None, Field(min_length=1, max_length=50000)] = None
    authentication: AuthType | None = None

# @dataclass
class Tool(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: Annotated[str, Field(min_length=1, max_length=200)]
    description: Annotated[str, Field(min_length=1, max_length=10000)]
    input_schema: dict[str, str]
    execution_config: ExecutionConfig
    response_transform: Annotated[str, Field(min_length=1, max_length=10000)]
    timeout_ms: Annotated[int, Field(ge=0, le=20000)]

# @dataclass
class Mcp(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: Annotated[str | None, Field(min_length=1, max_length=200)] = None
    name: Annotated[str, Field(min_length=1, max_length=500)]
    slug: Annotated[str, Field(min_length=1, max_length=60)]
    description: Annotated[str | None, Field(min_length=1, max_length=5000)] = None
    api_key: Annotated[str, Field(min_length=1, max_length=100)]
    tools: list[Tool]
    created_at: datetime | None = None
    updated_at: datetime | None = None
    archived_at: datetime | None = None

class McpSearchRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    ids: list[str] | None = None
    name: str | None = None
    slug: str | None = None
    description: str | None = None
    tools_name: str | None = None
    tools_description: str | None = None
    created_at_from: datetime | None = None
    created_at_to: datetime | None = None
    updated_at_from: datetime | None = None
    updated_at_to: datetime | None = None
    archived_at_from: datetime | None = None
    archived_at_to: datetime | None = None
    has_archived_at: bool | None = None
