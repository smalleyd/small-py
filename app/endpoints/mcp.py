from fastapi import APIRouter, Body, Depends, Query
from ..dao.startup import mcp_dao
from ..elastic.dao import Results
from ..models.common import Result
from .helpers import do_patch_validation
from ..models.mcp import *
from ..security import auth, auth_admin

dao = mcp_dao

router = APIRouter(prefix="/mcp", tags=["MCP"])

@router.get("/{id}", response_model_exclude_none=True, dependencies=[Depends(auth)])
async def get(id: str) -> Mcp:
    return dao.get(id)

@router.get("/", response_model_exclude_none=True, dependencies=[Depends(auth)])
async def find(value: Annotated[McpSearchRequest, Query()]) -> Results[Mcp]:
    return dao.search(value)

@router.get("/scroll/{id}", response_model_exclude_none=True, dependencies=[Depends(auth)])
async def scroll(id: str, time: str = "30s") -> Results[Mcp]:
    return dao.scroll(id, time)

@router.get("/slugs/{slug}", response_model_exclude_none=True, dependencies=[Depends(auth)])
async def get_by_slug(slug: str) -> Mcp:
    return dao.get_by_slug(slug)

@router.get("/slugs/{slug}/exists", dependencies=[Depends(auth)])
async def has_slug(slug: str) -> Result[bool]:
    return Result[bool](value=dao.has_slug(slug))

@router.post("/", status_code=201, dependencies=[Depends(auth)])
async def add(value: Mcp) -> Mcp:
    return dao.upsert(value)

@router.put("/", dependencies=[Depends(auth_admin)])
async def set(value: Mcp) -> Mcp:
    return await add(value)

@router.put("/{id}/tools", status_code=204, dependencies=[Depends(auth)])
async def set_tools(id: str, values: list[Tool]):
    dao.set_tools(id, values)

@router.patch("/{id}", dependencies=[Depends(auth)])
async def patch(id: str, value: Annotated[dict[str, Any], Body(min_length=1)]) -> Mcp:
    dao.patch(id, do_patch_validation(value, Mcp))

    return dao.get(id)

@router.delete("/{id}", status_code=204, dependencies=[Depends(auth_admin)])
async def delete(id: str) -> None:
    dao.remove(id)

@router.delete("/{id}/archive", status_code=204, dependencies=[Depends(auth)])
async def archive(id: str) -> None:
    dao.archive(id)