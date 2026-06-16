from dataclasses import dataclass
from typing import Generic, TypeVar

E = TypeVar("E")

@dataclass
class Result(Generic[E]):
    value: E
