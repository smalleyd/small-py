from enum import Enum
from pydantic import BaseModel, EmailStr, Field, HttpUrl # , AfterValidator
from typing import Annotated
from uuid import UUID, uuid4

class Color(Enum):
  Red="Red"
  Green="Green"
  Blue="Blue"

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
