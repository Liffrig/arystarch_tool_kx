from .point import Point
from .rectangle import Rectangle


def segments_intersect(p1: Point, p2: Point, p3: Point, p4: Point) -> bool:
    """Check if line segment p1-p2 intersects with segment p3-p4."""
    def ccw(a: Point, b: Point, c: Point) -> bool:
        return (c.y - a.y) * (b.x - a.x) > (b.y - a.y) * (c.x - a.x)

    return ccw(p1, p3, p4) != ccw(p2, p3, p4) and ccw(p1, p2, p3) != ccw(p1, p2, p4)


def line_intersects_rect(p1: Point, p2: Point, rect: Rectangle) -> bool:
    """Check if line segment intersects rectangle interior."""
    for e1, e2 in rect.get_edges():
        if segments_intersect(p1, p2, e1, e2):
            return True

    mid = Point((p1.x + p2.x) / 2, (p1.y + p2.y) / 2)
    if rect.does_collide(mid):
        return True

    return False