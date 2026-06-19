from ..datasource import es
from .mcp import McpDAO
from .person import PersonDAO

mcp_dao = McpDAO(es)
person_dao = PersonDAO(es)
