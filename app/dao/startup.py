from ..datasource import es
from .mcp import McpDAO
from .person import PersonDAO
from .session import SessionDAO

mcp_dao = McpDAO(es)
person_dao = PersonDAO(es)
session_dao = SessionDAO(es)