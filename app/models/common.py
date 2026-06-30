from pydantic import BaseModel
from dataclasses import dataclass
from typing import Generic, TypeVar

HEADER_API_KEY = "X-Contextly-Key"

E = TypeVar("E")

class Named(BaseModel):
    id: str
    name: str

@dataclass
class Result(Generic[E]):
    value: E
