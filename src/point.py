import math
from dataclasses import dataclass
from typing import Optional


@dataclass
class Point:
    x: float
    y: float
    label: Optional[str] = None

    def as_tuple(self) -> tuple[float, float]:
        return (self.x, self.y)

    def distance_to(self, other: 'Point') -> float:
        return math.sqrt((other.x - self.x)**2 + (other.y - self.y)**2)

    @classmethod
    def from_dict(cls, data: dict) -> 'Point':
        return cls(x=data["x"], y=data["y"], label=data.get("label"))

    @classmethod
    def from_tuple(cls, t: tuple[float, float], label: Optional[str] = None) -> 'Point':
        return cls(x=t[0], y=t[1], label=label)