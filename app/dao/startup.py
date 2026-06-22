from .mcp import McpDAO
from .otp import OtpDAO
from .person import PersonDAO
from .session import SessionDAO
from ..datasource import es, redis

mcp_dao = McpDAO(es)
otp_dao = OtpDAO(redis)
person_dao = PersonDAO(es)
session_dao = SessionDAO(es)