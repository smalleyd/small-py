from typing import Annotated, Any
from ..elastic.dao import Results
from ..security import auth, auth_admin
from .helpers import do_patch_validation
from fastapi import APIRouter, Depends, Query
from ..dao.startup import person_dao, session_dao
from ..models.person import Person, PersonSearchRequest

dao = person_dao
router = APIRouter(prefix="/people", tags=["People"])

@router.get("/{id}", response_model_exclude_none=True, dependencies=[Depends(auth)])
async def get(id: str) -> Person:
    return dao.get(id)

@router.get("/", response_model_exclude_none=True, dependencies=[Depends(auth_admin)])
async def find(filter_: Annotated[PersonSearchRequest, Query()]) -> Results[Person]:
    return dao.search(filter_)

@router.get("/scroll/{id}", response_model_exclude_none=True, dependencies=[Depends(auth_admin)])
async def scroll(id: str, time: str = "30s") -> Results[Person]:
    return dao.scroll(id, time)

@router.post("/", status_code = 201, dependencies=[Depends(auth_admin)])
async def add(value: Person) -> Person:
    return dao.upsert(value)

@router.put("/", dependencies=[Depends(auth_admin)])
async def set(value: Person) -> Person:
    return await add(value)

@router.patch("/{id}", dependencies=[Depends(auth)])
async def patch(id: str, value: dict[str, Any]) -> Person:
    dao.patch(id, do_patch_validation(value, Person))

    return dao.get(id)

@router.delete("/{id}", status_code=204, dependencies=[Depends(auth_admin)])
async def delete(id: str):
    dao.remove(id)
    session_dao.remove_by_person(id)

@router.delete("/{id}/archive", status_code=204, dependencies=[Depends(auth_admin)])
async def archive(id: str):
    dao.archive(id)
    session_dao.remove_by_person(id)
