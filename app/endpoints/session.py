from typing import Annotated, Any
from ..elastic.dao import Results
from ..models.common import Result
from ..dao.startup import session_dao
from ..security import auth, auth_admin
from .helpers import do_patch_validation
from fastapi.responses import JSONResponse
from fastapi import APIRouter, Depends, Query
from ..models.session import Session, SessionSearchRequest

dao = session_dao
router = APIRouter(prefix="/sessions", tags=["Session"])

@router.get("/{id}", response_model_exclude_none=True, dependencies=[Depends(auth)])
async def get(id: str) -> Session:
    return dao.get(id)

@router.get("/", response_model_exclude_none=True, dependencies=[Depends(auth_admin)])
async def find(filter_: Annotated[SessionSearchRequest, Query()]) -> Results[Session]:
    return dao.search(filter_)

@router.get("/scroll/{id}", response_model_exclude_none=True, dependencies=[Depends(auth_admin)])
async def scroll(id: str, time: str = "30s") -> Results[Session]:
    return dao.scroll(id, time)

@router.post("/", status_code=201, dependencies=[Depends(auth_admin)])
async def add(value: Session) -> Session:
    return dao.upsert(value)

@router.post("/api", response_model=Session, summary="Generate API Key", description="Generates a durable API key.")
async def generate_api_key(session: Annotated[Session, Depends(auth)]) -> JSONResponse:
    o = dao.get_durable_by_person(session.person.id)
    if o: return JSONResponse(status_code=200, content=o.model_dump(mode="json"))

    return  JSONResponse(
        status_code=201,
        content=dao.upsert(Session(person=session.person, duration=None, expires_at=None)).model_dump(mode="json"))

@router.put("/", dependencies=[Depends(auth_admin)])
async def set(value: Session) -> Session:
    return await add(value)

@router.patch("/{id}", dependencies=[Depends(auth_admin)])
async def patch(id: str, value: dict[str, Any]) -> Session:
    dao.patch(id, do_patch_validation(value, Session))

    return dao.get(id)

@router.delete("/clean", dependencies=[Depends(auth_admin)], summary="Clean", description="Removes expired sessions.")
async def clean() -> Result[int]:   # MUST put this before the delete_by_id below.
    return Result(value=dao.clean())

@router.delete("/{id}", status_code=204, dependencies=[Depends(auth)])
async def delete(id: str):
    dao.remove(id)
