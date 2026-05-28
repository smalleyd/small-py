from enum import Enum
from fastapi import FastAPI, Body, Depends, HTTPException, Query, Response	# ,Form, Path, HTTPException
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.security import APIKeyHeader, OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr, Field, HttpUrl # , AfterValidator
from typing import Annotated, Any
from uuid import UUID, uuid4

# auth = APIKeyHeader(name="x-context-key")
auth = OAuth2PasswordBearer(tokenUrl="auth")
app = FastAPI(title="My Context", version="0.0.1")	# , dependencies=[Depends(auth)]

class Color(Enum):
  Red="Red"
  Green="Green"
  Blue="Blue"

class AccessToken(BaseModel):
  access_token: str
  token_type: str = "bearer"

class Thing(BaseModel):
  model_config = {"extra": "forbid"} # https://fastapi.tiangolo.com/tutorial/query-param-models/#forbid-extra-query-parameters

  id: UUID = Field(default=uuid4())
  email: EmailStr
  name: str = Field(examples=["Some Thing 1"])
  color: Color
  less: bool
  more: bool
  tags: Annotated[list[str] | None, Field(title="My Tags", description="The tags of a Thing", max_length=2)]	# Additional Query params: alias, deprecated, include_in_schema
  num_of_days: Annotated[int, Field(ge=3, lt=20)]
  url: HttpUrl | None = Field(default=None, examples=["https://www.thing.com/first"])

@app.post("/auth", tags=["Person"])
async def authenticate(value: Annotated[OAuth2PasswordRequestForm, Depends()]) -> AccessToken:
  print(f"AUTH: {value}")
  username = value.username
  password = value.password
  if not username or username != "api" or not password:
    raise HTTPException(status_code=422, detail="Invalid credentials")

  return AccessToken(access_token=password)

@app.get("/", response_model_exclude_unset=True, tags=["Things"])
async def root():
  return {"message":"Hello World"}

@app.get("/thing/{id}", response_model_exclude_unset=True, dependencies=[Depends(auth)], tags=["Things"])	# , dependencies=[Depends(function)] ,response_model: not needed
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

@app.post("/thing", dependencies=[Depends(auth)], response_model_exclude_unset=True, response_model_exclude_none=True, response_model_exclude=["tags"], status_code=201, tags=["Things"])
async def postThing(value: Thing) -> Thing:
  return value

@app.put("/thing/{id}", response_model_exclude_unset=True, tags=["Things"])
async def putThing(id: str,
  value: Annotated[Thing, Body(embed=True)]) -> Thing:
    return value

@app.put("/things", response_model=Thing, response_model_exclude_none=True, tags=["Things"])
async def putThings(value: Thing) -> Response:
  # return JSONResponse(content=value.model_dump(exclude=["id", "color", "url"]), status_code=202)
  return JSONResponse(content=jsonable_encoder(value), status_code=202)

@app.patch("/things/{id}", response_model_exclude_unset=True, tags=["Things"])
async def patchThings(id: str, value: Thing) -> Thing:
  return value.model_dump(exclude_unset=True)
