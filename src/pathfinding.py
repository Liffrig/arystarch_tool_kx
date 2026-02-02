"""Pathfinding algorithms for obstacle avoidance."""

from heapq import heappush, heappop
from typing import Optional

from .point import Point
from .rectangle import Rectangle
from .geo_helpers import line_intersects_rect


def has_line_of_sight(p1: Point, p2: Point, obstacles: list[Rectangle]) -> bool:
    """Check if there's clear line of sight between two points."""
    for obs in obstacles:
        if line_intersects_rect(p1, p2, obs):
            return False
    return True


def is_valid_waypoint(p: Point, obstacles: list[Rectangle], boundary: Rectangle) -> bool:
    """Check if waypoint is valid (inside boundary, not inside any obstacle)."""
    if not boundary.is_on_edge(p):
        return False

    for obs in obstacles:
        if obs.does_collide(p):
            return False
    return True


def find_shortest_path(
    start: Point,
    end: Point,
    obstacles: list[Rectangle],
    boundary: Rectangle
) -> Optional[list[Point]]:
    """
    Find shortest path from start to end avoiding obstacles.
    Uses visibility graph + Dijkstra's algorithm.
    """
    # Direct line of sight - return direct path
    if has_line_of_sight(start, end, obstacles):
        return [start, end]

    # Build waypoints from obstacle corners
    waypoints: list[Point] = []
    for obs in obstacles:
        waypoints.extend(obs.get_waypoints())

    # Filter valid waypoints
    waypoints = [w for w in waypoints if is_valid_waypoint(w, obstacles, boundary)]

    # All nodes: start + end + waypoints
    nodes = [start, end] + waypoints

    # Build visibility graph
    graph: dict[int, list[tuple[int, float]]] = {i: [] for i in range(len(nodes))}

    for i in range(len(nodes)):
        for j in range(i + 1, len(nodes)):
            if has_line_of_sight(nodes[i], nodes[j], obstacles):
                d = nodes[i].distance_to(nodes[j])
                graph[i].append((j, d))
                graph[j].append((i, d))

    # Dijkstra's algorithm
    dist: dict[int, float] = {i: float('inf') for i in range(len(nodes))}
    prev: dict[int, Optional[int]] = {i: None for i in range(len(nodes))}
    dist[0] = 0.0

    pq: list[tuple[float, int]] = [(0.0, 0)]

    while pq:
        d, u = heappop(pq)

        if d > dist[u]:
            continue

        if u == 1:  # reached end
            break

        for v, w in graph[u]:
            if dist[u] + w < dist[v]:
                dist[v] = dist[u] + w
                prev[v] = u
                heappush(pq, (dist[v], v))

    # Reconstruct path
    if dist[1] == float('inf'):
        return None

    path: list[Point] = []
    node: Optional[int] = 1
    while node is not None:
        path.append(nodes[node])
        node = prev[node]

    path.reverse()
    return path


def check_point_location(
    point: Point,
    boundary: Rectangle,
    squares: list[Rectangle]
) -> dict:
    """Check if a point is inside the boundary and which squares it's in."""
    result = {
        'inside_boundary': boundary.is_on_edge(point),
        'inside_squares': []
    }

    for square in squares:
        if square.does_collide(point):
            result['inside_squares'].append(square.label or "unnamed")

    return result