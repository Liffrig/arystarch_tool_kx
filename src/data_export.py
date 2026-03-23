import pandas as pd
from pathlib import Path

def export_points(
        df: pd.DataFrame,
        area: str,
        x_col: str = "Position X",
        y_col: str = "Position Y",
        file_col: str = "source_file",
) -> dict:

    d = df.copy()
    points = []

    # append waypoint  {"x":	26.66,	"y":	24.19, "label":	"WP_CD1"}
    wp_value = d.query(f"Name == 'WAYPOINT' and ID == '{area}'")
    label = f'WP_{area}'
    points.append({"x": float(wp_value[x_col].values[0]), "y": float(wp_value[y_col].values[0]), "label": label})

    # append all other points
    all_points = d[d[file_col].str.endswith(f"{area}.xlsx") & (d["Name"] != 'BMARKER') & (d["ROW"].notna())]

    for inx, r in all_points.iterrows():
        points.append({"x": float(r[x_col]), "y": float(r[y_col]), "label": r["ROW"].upper() + r["ID"].upper()})

    result = {"points": points}
    return result

def export_bmarkers(
    df: pd.DataFrame,
    area: str,
    x_col: str = "Position X",
    y_col: str = "Position Y",
    file_col: str = "source_file",
    rack_col: str = "unique_rack"
) -> dict:
    d = df.copy()

    d[x_col] = pd.to_numeric(d[x_col], errors="coerce")
    d[y_col] = pd.to_numeric(d[y_col], errors="coerce")

    d = d.dropna(subset=[x_col, y_col, file_col, rack_col])

    squares = []
    problems = []

    for (source_file, unique_rack), g in d.groupby([file_col, rack_col], sort=False):
        if len(g) != 2:
            problems.append({
                "source_file": source_file,
                "unique_rack": unique_rack,
                "rows_found": len(g)
            })
            continue


        p1 = g.iloc[0]
        p2 = g.iloc[1]

        squares.append({
            "label": f"{area}_{unique_rack}",
            "corners": [
                {"x": float(p1[x_col]), "y": float(p1[y_col])},
                {"x": float(p2[x_col]), "y": float(p2[y_col])},
            ]
        })

    result = {"squares": squares}

    if problems:
        print("Skipped racks:")
        try:
            print(pd.DataFrame(problems))
        except NameError:
            print(problems)
    return result
