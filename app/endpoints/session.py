from ..security import auth
from typing import Annotated, Any
from ..elastic.dao import Results
from ..dao.startup import session_dao
from .helpers import do_patch_validation
from fastapi import APIRouter, Depends, Query
from ..models.session import Session, SessionSearchRequest

dao = session_dao
router = APIRouter(prefix="/sessions", tags=["Session"], dependencies=[Depends(auth)])

@router.get("/{id}", response_model_exclude_none=True)
async def get(id: str) -> Session:
    return dao.get(id)

@router.get("/", response_model_exclude_none=True)
async def find(filter_: Annotated[SessionSearchRequest, Query()]) -> Results[Session]:
    return dao.search(filter_)

@router.get("/scroll/{id}", response_model_exclude_none=True)
async def scroll(id: str, time: str = "30s") -> Results[Session]:
    return dao.scroll(id, time)

@router.post("/", status_code=201)
async def add(value: Session) -> Session:
    return dao.upsert(value)

@router.put("/")
async def set(value: Session) -> Session:
    return await add(value)

@router.patch("/{id}")
async def patch(id: str, value: dict[str, Any]) -> Session:
    dao.patch(id, do_patch_validation(value, Session))

    return dao.get(id)

@router.delete("/{id}", status_code=204)
async def delete(id: str):
    dao.remove(id)