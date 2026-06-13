from enum import Enum
from datetime import datetime
from dataclasses import dataclass
from pydantic import BaseModel

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

@dataclass
class ExecutionConfig():
    url: str
    method: Method
    headers: dict[str, str]
    body_template: str | None = None
    authentication: AuthType | None = None

@dataclass
class Tool():
    name: str
    description: str
    input_schema: dict[str, str]
    execution_config: ExecutionConfig
    response_transform: str
    timeout_ms: int

@dataclass
class Mcp():
    id: str
    name: str
    slug: str
    description: str
    api_key: str
    tools: list[Tool]
    created_at: datetime
    updated_at: datetime
    archived_at: datetime | None = None

class McpSearchRequest(BaseModel):
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
