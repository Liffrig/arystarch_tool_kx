import json
import math
import sys
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from concurrent.futures import ThreadPoolExecutor
from typing import Optional
from pathlib import Path

from src.point import Point
from src.rectangle import Rectangle
from src.pathfinding import find_shortest_path
from config import CANVAS_WIDTH, CANVAS_HEIGHT, PADDING, POINT_RADIUS, WAYPOINT_RADIUS, POINT_COLOUR, NICE_COLOURS
from exporter import calculate_all_paths, export_paths


class CoordinateVisualizer:
    def __init__(self, root):
        self.root = root
        self.root.title("Coordinate Visualizer")

        self.canvas_width = CANVAS_WIDTH
        self.canvas_height = CANVAS_HEIGHT
        self.padding = PADDING

        # Future batch execution
        self.executor = ThreadPoolExecutor(max_workers=4)

        # menu
        menubar = tk.Menu(root)
        filemenu = tk.Menu(menubar, tearoff=0)
        filemenu.add_command(label="Open JSON...", command=self.load_file)
        filemenu.add_separator()
        filemenu.add_command(label="Exit", command=root.quit)
        menubar.add_cascade(label="File", menu=filemenu)
        root.config(menu=menubar)

        # all the gui shit
        control_frame = tk.Frame(root)
        control_frame.pack(pady=5, fill=tk.X, padx=10)

        tk.Label(control_frame, text="From:").pack(side=tk.LEFT, padx=5)
        self.from_var = tk.StringVar()
        self.from_dropdown = ttk.Combobox(control_frame, textvariable=self.from_var, state="readonly", width=15)
        self.from_dropdown.pack(side=tk.LEFT, padx=5)
        self.from_dropdown.bind("<<ComboboxSelected>>", self.on_path_change)

        tk.Label(control_frame, text="To:").pack(side=tk.LEFT, padx=5)
        self.to_var = tk.StringVar()
        self.to_dropdown = ttk.Combobox(control_frame, textvariable=self.to_var, state="readonly", width=15)
        self.to_dropdown.pack(side=tk.LEFT, padx=5)
        self.to_dropdown.bind("<<ComboboxSelected>>", self.on_path_change)

        self.path_label = tk.Label(control_frame, text="")
        self.path_label.pack(side=tk.LEFT, padx=20)

        # Export button
        self.export_btn = tk.Button(control_frame, text="Export All Paths", command=self.export_all_paths)
        self.export_btn.pack(side=tk.RIGHT, padx=5)

        self.canvas = tk.Canvas(
            root,
            width=self.canvas_width,
            height=self.canvas_height,
            bg="white"
        )
        self.canvas.pack(padx=10, pady=10)

        self.status = tk.Label(root, text="Load a JSON file to visualize")
        self.status.pack(pady=5)

        self.data = None
        self.boundary: Optional[Rectangle] = None
        self.obstacles: list[Rectangle] = []
        self.points: list[Point] = []
        self.current_path: Optional[list[Point]] = None

        self.view_min_x = 0.0
        self.view_max_x = 100.0
        self.view_min_y = 0.0
        self.view_max_y = 100.0

    def load_file(self, filepath=None):
        if filepath is None:
            filepath = filedialog.askopenfilename(
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
            )

        if not filepath:
            return

        # jeśli możesz to nie testuj ładowania różnych dzwinych plików...
        try:
            with open(filepath, 'r') as f:
                self.data = json.load(f)
            self.parse_et_draw()
            self.status.config(text=f"Loaded: {filepath}")
        except FileNotFoundError:
            messagebox.showerror("Error", f"File not found: {filepath}")
        except json.JSONDecodeError as e:
            messagebox.showerror("Error", f"Invalid JSON: {e}")
        except Exception as e:
            messagebox.showerror("Error", f"Error loading file: {e}")

    def parse_et_draw(self):
        self.canvas.delete("all")
        self.current_path = None

        # boundaries
        raw_corners = self.data.get("corners", [])
        if len(raw_corners) not in (2, 4):
            messagebox.showerror("Error", "Expected 2 or 4 corners for the main boundary")
            return

        boundary_corners = [Point.from_dict(c) for c in raw_corners]
        self.boundary = Rectangle(corners=boundary_corners, label="Boundary")

        # racks
        self.obstacles = []
        for i, sq_data in enumerate(self.data.get("squares", [])):
            try:
                rect = Rectangle.from_dict(sq_data)
                if rect.label is None:
                    rect.label = f"Square {i + 1}"
                self.obstacles.append(rect)
            except ValueError as e:
                messagebox.showerror("Error", f"Square {i}: {e}")
                return

        # pick points
        self.points = [Point.from_dict(p) for p in self.data.get("points", [])]
        point_labels = [p.label or f"({p.x}, {p.y})" for p in self.points]
        self.from_dropdown['values'] = point_labels
        self.to_dropdown['values'] = point_labels

        if point_labels:
            self.from_dropdown.current(0)
            if len(point_labels) > 1:
                self.to_dropdown.current(1)
            else:
                self.to_dropdown.current(0)

        # resize view to boundaries
        margin = 0.05 * max(
            self.boundary.max_x - self.boundary.min_x,
            self.boundary.max_y - self.boundary.min_y
        )
        self.view_min_x = self.boundary.min_x - margin
        self.view_max_x = self.boundary.max_x + margin
        self.view_min_y = self.boundary.min_y - margin
        self.view_max_y = self.boundary.max_y + margin

        self.redraw()
        self.on_path_change(None)

    def redraw(self):
        self.canvas.delete("all")
        self.draw_grid()
        self.draw_rectangles()

        if self.current_path:
            self.draw_path(self.current_path)

        self.draw_points()

    def transform_coords(self, x: float, y: float) -> tuple[float, float]:
        """Transform data coordinates to canvas coordinates."""
        canvas_x = self.padding + (x - self.view_min_x) / (self.view_max_x - self.view_min_x) * (self.canvas_width - 2 * self.padding)
        canvas_y = self.canvas_height - self.padding - (y - self.view_min_y) / (self.view_max_y - self.view_min_y) * (self.canvas_height - 2 * self.padding)
        return canvas_x, canvas_y

    def draw_rectangle(self, rect: Rectangle, color: str, width: int, show_label: bool = True, show_corners: bool = True):
        # sort corners by angle for proper drawing order
        centroid = rect.center
        sorted_corners = sorted(
            rect.corners,
            key=lambda c: math.atan2(c.y - centroid.y, c.x - centroid.x)
        )

        # draw edges
        for i in range(4):
            c1 = sorted_corners[i]
            c2 = sorted_corners[(i + 1) % 4]
            x1, y1 = self.transform_coords(c1.x, c1.y)
            x2, y2 = self.transform_coords(c2.x, c2.y)
            self.canvas.create_line(x1, y1, x2, y2, fill=color, width=width)

        # Draw corner markers
        if show_corners:
            for corner in rect.corners:
                x, y = self.transform_coords(corner.x, corner.y)
                r = WAYPOINT_RADIUS
                self.canvas.create_oval(x - r, y - r, x + r, y + r, fill=color, outline="black")
                if corner.label:
                    self.canvas.create_text(x, y - 12, text=corner.label, fill=color, font=("Arial", 9, "bold"))

        # Draw label at centroid
        if show_label and rect.label:
            cx, cy = self.transform_coords(centroid.x, centroid.y)
            self.canvas.create_text(cx, cy, text=rect.label, fill=color, font=("Arial", 10, "bold"))

    def draw_rectangles(self):
        """Draw boundary and obstacles."""
        if self.boundary:
            self.draw_rectangle(self.boundary, "black", 3, show_label=False, show_corners=True)

        for idx, obs in enumerate(self.obstacles):
            color = NICE_COLOURS[idx % len(NICE_COLOURS)]
            self.draw_rectangle(obs, color, 2, show_label=True, show_corners=False)

    def draw_grid(self):
        """Draw light grid lines."""
        x_range = self.view_max_x - self.view_min_x
        y_range = self.view_max_y - self.view_min_y

        for i in range(11):
            x = self.view_min_x + i * x_range / 10
            x1, y1 = self.transform_coords(x, self.view_min_y)
            x2, y2 = self.transform_coords(x, self.view_max_y)
            self.canvas.create_line(x1, y1, x2, y2, fill="#e0e0e0")

        for i in range(11):
            y = self.view_min_y + i * y_range / 10
            x1, y1 = self.transform_coords(self.view_min_x, y)
            x2, y2 = self.transform_coords(self.view_max_x, y)
            self.canvas.create_line(x1, y1, x2, y2, fill="#e0e0e0")

    def draw_points(self):
        """Draw all points."""
        for point in self.points:
            x, y = self.transform_coords(point.x, point.y)
            r = POINT_RADIUS
            self.canvas.create_oval(x - r, y - r, x + r, y + r, fill=POINT_COLOUR, outline="darkred")
            label = point.label or f"({point.x}, {point.y})"
            self.canvas.create_text(x + 10, y - 10, text=label, fill="black", font=("Arial", 10, "bold"), anchor="w")

    def draw_path(self, path: list[Point]):
        """Draw the calculated path."""
        if len(path) < 2:
            return

        # Draw path segments
        for i in range(len(path) - 1):
            x1, y1 = self.transform_coords(path[i].x, path[i].y)
            x2, y2 = self.transform_coords(path[i + 1].x, path[i + 1].y)
            self.canvas.create_line(x1, y1, x2, y2, fill="red", width=3, dash=(5, 3))

        # Draw intermediate waypoints
        for i, point in enumerate(path):
            if 0 < i < len(path) - 1:
                x, y = self.transform_coords(point.x, point.y)
                r = WAYPOINT_RADIUS
                self.canvas.create_oval(x - r, y - r, x + r, y + r, fill="purple", outline="purple")

    def on_path_change(self, _event):
        """Handle dropdown selection change."""
        from_idx = self.from_dropdown.current()
        to_idx = self.to_dropdown.current()

        if from_idx < 0 or to_idx < 0 or not self.points:
            return

        start = self.points[from_idx]
        end = self.points[to_idx]

        # Async pathfinding
        future = self.executor.submit(
            find_shortest_path, start, end, self.obstacles, self.boundary
        )
        self.root.after(10, lambda: self.check_path_result(future))

    def check_path_result(self, future):
        """Check if async path calculation is done."""
        if future.done():
            try:
                self.current_path = future.result()
                if self.current_path:
                    total_dist = sum(
                        self.current_path[i].distance_to(self.current_path[i + 1])
                        for i in range(len(self.current_path) - 1)
                    )
                    self.path_label.config(text=f"Path length: {total_dist:.2f}")
                else:
                    self.path_label.config(text="No valid path found")
                self.redraw()
            except Exception as e:
                self.path_label.config(text=f"Error: {e}")
        else:
            self.root.after(10, lambda: self.check_path_result(future))

    def export_all_paths(self):
        """Export all point-to-point path calculations to .txt and .pkl files."""
        if not self.points:
            messagebox.showwarning("Warning", "No points loaded. Load a JSON file first.")
            return

        if len(self.points) < 2:
            messagebox.showwarning("Warning", "Need at least 2 points to calculate paths.")
            return

        def on_progress(done, total):
            self.status.config(text=f"Calculating paths: {done}/{total}")
            self.root.update()

        self.status.config(text="Calculating paths: 0/...")
        self.root.update()

        try:
            results = calculate_all_paths(
                self.points, self.obstacles, self.boundary, self.executor, on_progress
            )
            txt_path, pkl_path = export_paths(results, self.points, Path(__file__).parent / "reports")
            self.status.config(text=f"Exported to: {txt_path.name}, {pkl_path.name}")
            messagebox.showinfo("Success", f"Paths exported to:\n{txt_path}\n{pkl_path}")
        except Exception as e:
            self.status.config(text=f"Export failed: {e}")
            messagebox.showerror("Error", f"Failed to export: {e}")


def main():
    root = tk.Tk()
    app = CoordinateVisualizer(root)

    if len(sys.argv) > 1:
        root.after(100, lambda: app.load_file(sys.argv[1]))

    root.mainloop()


if __name__ == "__main__":
    main()