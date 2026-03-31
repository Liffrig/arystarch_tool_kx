import json
from pathlib import Path

CANVAS_WIDTH = 800
CANVAS_HEIGHT = 700
PADDING = 50

POINT_RADIUS = 6
WAYPOINT_RADIUS = 4
POINT_COLOUR = "orange"

_colours_path = Path(__file__).parent / "colors.json"
with open(_colours_path) as _f:
    NICE_COLOURS: list[str] = json.load(_f)["obstacle_colours"]