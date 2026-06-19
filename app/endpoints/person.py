from ..security import auth
from typing import Annotated, Any
from ..elastic.dao import Results
from ..dao.startup import person_dao
from .helpers import do_patch_validation
from fastapi import APIRouter, Depends, Query
from ..models.person import Person, PersonSearchRequest

dao = person_dao
router = APIRouter(prefix="/people", tags=["People"], dependencies=[Depends(auth)])

@router.get("/{id}", response_model_exclude_none=True)
async def get(id: str) -> Person:
    return dao.get(id)

@router.get("/", response_model_exclude_none=True)
async def find(filter_: Annotated[PersonSearchRequest, Query()]) -> Results[Person]:
    return dao.search(filter_)

@router.get("/scroll/{id}", response_model_exclude_none=True)
async def scroll(id: str, time: str = "30s") -> Results[Person]:
    return dao.scroll(id, time)

@router.post("/", status_code = 201)
async def add(value: Person) -> Person:
    return dao.upsert(value)

@router.put("/")
async def set(value: Person) -> Person:
    return await add(value)

@router.patch("/{id}")
async def patch(id: str, value: dict[str, Any]) -> Person:
    dao.patch(id, do_patch_validation(value, Person))

    return dao.get(id)

@router.delete("/{id}", status_code=204)
async def delete(id: str):
    dao.remove(id)

@router.delete("/{id}/archive", status_code=204)
async def archive(id: str):
    dao.archive(id)