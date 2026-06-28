from pydantic import BaseModel
from dataclasses import dataclass
from typing import Generic, TypeVar

E = TypeVar("E")

class Named(BaseModel):
    id: str
    name: str

@dataclass
class Result(Generic[E]):
    value: E
