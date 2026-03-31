import pickle
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path
from typing import Callable, Optional

from src.point import Point
from src.rectangle import Rectangle
from src.pathfinding import find_shortest_path


def calculate_all_paths(
    points: list[Point],
    obstacles: list[Rectangle],
    boundary: Rectangle,
    executor: ThreadPoolExecutor,
    on_progress: Optional[Callable[[int, int], None]] = None,
) -> dict[tuple[int, int], tuple[Optional[list[Point]], float]]:
    futures = {}
    for i, p1 in enumerate(points):
        for j, p2 in enumerate(points):
            if i >= j:
                continue
            futures[(i, j)] = executor.submit(find_shortest_path, p1, p2, obstacles, boundary)

    results = {}
    total = len(futures)
    for idx, (key, future) in enumerate(futures.items()):
        path = future.result()
        dist = sum(path[k].distance_to(path[k + 1]) for k in range(len(path) - 1)) if path else -1.0
        results[key] = (path, dist)
        if on_progress:
            on_progress(idx + 1, total)

    return results


def export_paths(
    results: dict[tuple[int, int], tuple[Optional[list[Point]], float]],
    points: list[Point],
    output_dir: Path,
) -> tuple[Path, Path]:
    output_dir.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    txt_path = output_dir / f"paths_{timestamp}.txt"
    pkl_path = output_dir / f"paths_{timestamp}.pkl"

    with open(txt_path, 'w') as f:
        for (i, j), (path, dist) in sorted(results.items()):
            label1 = points[i].label or f"Point {i}"
            label2 = points[j].label or f"Point {j}"
            if path and dist >= 0:
                f.write(f"{label1} -> {label2}: {dist:.2f}\n")
            else:
                f.write(f"{label1} -> {label2}: NO PATH\n")

    pickle_data = {
        (points[i].label or f"Point {i}", points[j].label or f"Point {j}"): {
            "distance": dist,
            "waypoints": [(p.x, p.y) for p in path] if path else None,
        }
        for (i, j), (path, dist) in results.items()
    }
    with open(pkl_path, 'wb') as f:
        pickle.dump(pickle_data, f)

    return txt_path, pkl_path