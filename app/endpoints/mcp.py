from uuid import uuid4
from typing import Any
from fastapi import APIRouter, Body, Depends, Query
from ..dao.startup import mcp_dao
from ..elastic.dao import Results
from .helpers import do_patch_validation
from ..models.mcp import *
from ..security import auth

dao = mcp_dao

router = APIRouter(prefix="/mcp", tags=["MCP"], dependencies=[Depends(auth)])

@router.get("/{id}", response_model_exclude_none=True)
async def get(id: str) -> Mcp:
    return dao.get(id)

@router.get("/", response_model_exclude_none=True)
async def find(value: Annotated[McpSearchRequest, Query()]) -> Results[Mcp]:
    return dao.search(value)

@router.get("/scroll/{id}", response_model_exclude_none=True)
async def scroll(id: str, time: str = "30s") -> Results[Mcp]:
    return dao.scroll(id, time)

@router.post("/", status_code=201)
async def add(value: Mcp) -> Mcp:
    if not value.id: value.id = uuid4().hex
    return dao.upsert(value)

@router.put("/")
async def set(value: Mcp) -> Mcp:
    return await add(value)

@router.put("/{id}/tools", status_code=204)
async def set_tools(id: str, values: list[Tool]):
    dao.set_tools(id, values)

@router.patch("/{id}")
async def patch(id: str, value: Annotated[dict[str, Any], Body(min_length=1)]) -> Mcp:
    dao.patch(id, do_patch_validation(value, Mcp))

    return dao.get(id)

@router.delete("/{id}", status_code=204)
async def delete(id: str) -> None:
    dao.archive(id)