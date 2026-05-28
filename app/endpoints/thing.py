from fastapi import APIRouter, Body, Depends, Query, Response
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from pydantic import EmailStr,  HttpUrl
from typing import Annotated
from ..security import auth
from ..models.thing import *

router = APIRouter(prefix="/things", tags=["Things"], dependencies=[Depends(auth)])

@router.get("/{id}", response_model_exclude_unset=True)
async def getThing(
  id: str,
  email: EmailStr,
  less: bool,
  color: Color,
  num_of_days: Annotated[int, Query(ge=3, lt=20)],
  name: Annotated[str | None, Query(min_length=1, max_length=50)] = None,
  more: bool = False,
  tags: Annotated[list[str] | None, Query(max_length=2)] = None) -> Thing:
    print(tags)
    name_ = name if name else f"Thing {id}"
    return Thing(id=id, name=name_, color=color, less=less, more=more, tags=tags, num_of_days=num_of_days)

@router.post("/", response_model_exclude_unset=True, response_model_exclude_none=True, response_model_exclude=["tags"], status_code=201)
async def postThing(value: Thing) -> Thing:
  return value

@router.put("/{id}", response_model_exclude_unset=True)
async def putThing(id: str,
  value: Annotated[Thing, Body(embed=True)]) -> Thing:
    return value

@router.put("/", response_model=Thing, response_model_exclude_none=True)
async def putThings(value: Thing) -> Response:
  # return JSONResponse(content=value.model_dump(exclude=["id", "color", "url"]), status_code=202)
  return JSONResponse(content=jsonable_encoder(value), status_code=202)

@router.patch("/{id}", response_model_exclude_unset=True)
async def patchThings(id: str, value: Thing) -> Thing:
  return value.model_dump(exclude_unset=True)
