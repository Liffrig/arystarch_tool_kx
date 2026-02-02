from dataclasses import dataclass, field
from typing import Optional

from .point import Point


@dataclass
class Rectangle:
    corners: list[Point] = field(default_factory=list)
    label: Optional[str] = None

    def __post_init__(self):
        """Expand 2 diagonal corners to 4"""
        if len(self.corners) == 2:
            c1, c2 = self.corners
            self.corners = [
                Point(c1.x, c1.y, c1.label),
                Point(c2.x, c1.y),
                Point(c2.x, c2.y, c2.label),
                Point(c1.x, c2.y),
            ]
        elif len(self.corners) != 4:
            raise ValueError(f"Rectangle must have 2 or 4 corners, got {len(self.corners)}")

    @property
    def min_x(self) -> float:
        return min(c.x for c in self.corners)

    @property
    def max_x(self) -> float:
        return max(c.x for c in self.corners)

    @property
    def min_y(self) -> float:
        return min(c.y for c in self.corners)

    @property
    def max_y(self) -> float:
        return max(c.y for c in self.corners)

    @property
    def bounds(self) -> tuple[float, float, float, float]:
        return (self.min_x, self.max_x, self.min_y, self.max_y)

    @property
    def center(self) -> Point:
        cx = sum(c.x for c in self.corners) / 4
        cy = sum(c.y for c in self.corners) / 4
        return Point(cx, cy)

    def does_collide(self, p: Point, margin: float = 0.001) -> bool:
        return (
            (self.min_x + margin) < p.x < (self.max_x - margin) and
            (self.min_y + margin) < p.y < (self.max_y - margin)
        )

    def is_on_edge(self, p: Point) -> bool:
        return (
            self.min_x <= p.x <= self.max_x and
            self.min_y <= p.y <= self.max_y
        )

    # Aliases
    contains_point = does_collide
    contains_point_inclusive = is_on_edge

    def get_edges(self) -> list[tuple[Point, Point]]:
        """Get rectangle edges as list of point pairs."""
        return [
            (Point(self.min_x, self.min_y), Point(self.max_x, self.min_y)),
            (Point(self.max_x, self.min_y), Point(self.max_x, self.max_y)),
            (Point(self.max_x, self.max_y), Point(self.min_x, self.max_y)),
            (Point(self.min_x, self.max_y), Point(self.min_x, self.min_y)),
        ]

    def get_waypoints(self, margin: float = 0.5) -> list[Point]:
        """Get corner waypoints with offset for pathfinding."""
        return [
            Point(self.min_x - margin, self.min_y - margin),
            Point(self.max_x + margin, self.min_y - margin),
            Point(self.max_x + margin, self.max_y + margin),
            Point(self.min_x - margin, self.max_y + margin),
        ]

    @classmethod
    def from_dict(cls, data: dict) -> 'Rectangle':
        corners = [Point.from_dict(c) for c in data.get("corners", [])]
        return cls(corners=corners, label=data.get("label"))