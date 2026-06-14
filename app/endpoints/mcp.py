from uuid import uuid4
from typing import Annotated, Any
from fastapi import APIRouter, Body, Depends, Query
from ..datasource import es
from ..dao.mcp import McpDAO
from ..elastic.dao import Results
from .helpers import do_patch_validation
from ..models.mcp import *
from ..security import auth

dao = McpDAO(es)
router = APIRouter(prefix="/mcp", tags=["MCP"], dependencies=[Depends(auth)])

@router.get("/{id}", response_model_exclude_none=True)
async def get(id: str) -> Mcp:
    return dao.get(id)

@router.get("/", response_model_exclude_none=True)
async def find(value: Annotated[McpSearchRequest, Query()]) -> Results[Mcp]:
    return dao.search(value)

@router.post("/", status_code=201)
async def add(value: Mcp) -> Mcp:
    if not value.id: value.id = uuid4().hex
    return dao.upsert(value)

@router.put("/")
async def update(value: Mcp) -> Mcp:
    return await add(value)

@router.patch("/{id}")
async def patch(id: str, value: Annotated[dict[str, Any], Body(min_length=1)]) -> Mcp:
    dao.patch(id, do_patch_validation(value, Mcp))

    return dao.get(id)

@router.delete("/{id}", status_code=204)
async def delete(id: str) -> None:
    dao.archive(id)