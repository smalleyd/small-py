from typing import Annotated, Any
from fastapi import APIRouter, Depends, Query
from ..datasource import es
from ..dao.mcp import McpDAO
from ..elastic.dao import Results
from ..models.mcp import *
from ..security import auth

dao = McpDAO(es)
router = APIRouter(prefix="/mcp", tags=["MCP"], dependencies=[Depends(auth)])

@router.get("/{id}")
async def get(id: str) -> Mcp:
    return dao.get(id)

@router.get("/")
async def find(value: Annotated[McpSearchRequest, Query()]) -> Results[Mcp]:
    return dao.search(value)

@router.post("/", status_code=201)
async def add(value: Mcp) -> Mcp:
    return dao.upsert(value)

@router.put("/{id}")
async def update(id: str, value: Mcp) -> Mcp:
    return dao.upsert(value)

@router.patch("/{id}")
async def patch(id: str, value: dict[str, Any]) -> Mcp:
    dao.patch(id, value)

    return dao.get(id)

@router.delete("/{id}", status_code=204)
async def delete(id: str) -> None:
    dao.remove(id)