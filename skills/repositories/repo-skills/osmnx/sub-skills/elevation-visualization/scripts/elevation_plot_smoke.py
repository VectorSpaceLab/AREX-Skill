#!/usr/bin/env python
"""Smoke test for OSMnx elevation and static plotting workflows.

The script builds a tiny graph, attaches elevations from a local raster when
raster support is available, computes edge grades, and optionally saves a few
headless plots. It avoids network calls and does not depend on the original
repository checkout.
"""

from __future__ import annotations

import argparse
import tempfile
from pathlib import Path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Exercise a tiny OSMnx graph with elevations, grades, and optional static plots.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Directory for any saved plot images. A temp directory is used when omitted.",
    )
    parser.add_argument(
        "--cpus",
        type=int,
        default=1,
        help="CPU cores to use for raster elevation sampling.",
    )
    parser.add_argument(
        "--multi-raster",
        action="store_true",
        help="Create two adjacent rasters and try the VRT-backed multi-raster path when raster support is available.",
    )
    parser.add_argument(
        "--plot",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Enable headless plotting smoke when matplotlib is available.",
    )
    parser.add_argument(
        "--raster",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Enable local raster elevation smoke when raster support is available.",
    )
    return parser


def build_demo_graph():
    import networkx as nx

    G = nx.MultiDiGraph(crs="EPSG:4326")
    nodes = {
        1: (0.25, 0.25, 1),
        2: (0.75, 0.25, 2),
        3: (0.75, 0.75, 2),
        4: (0.25, 0.75, 1),
    }
    for node_id, (x, y, street_count) in nodes.items():
        G.add_node(node_id, x=x, y=y, street_count=street_count)

    edges = [
        (1, 2),
        (2, 1),
        (2, 3),
        (3, 2),
        (3, 4),
        (4, 3),
        (4, 1),
        (1, 4),
    ]
    for osmid, (u, v) in enumerate(edges, start=1):
        G.add_edge(u, v, osmid=osmid, length=100.0, highway="residential")
    return G


def write_raster(path: Path, *, west: float, north: float, xsize: float, ysize: float, data) -> None:
    import numpy as np
    import rasterio
    from rasterio.transform import from_origin

    array = np.asarray(data, dtype="float32")
    transform = from_origin(west, north, xsize, ysize)
    path.parent.mkdir(parents=True, exist_ok=True)
    with rasterio.open(
        path,
        mode="w",
        driver="GTiff",
        height=array.shape[0],
        width=array.shape[1],
        count=1,
        dtype="float32",
        crs="EPSG:4326",
        transform=transform,
        nodata=-9999.0,
    ) as dst:
        dst.write(array, 1)


def attach_elevations(ox, G, output_dir: Path, *, multi_raster: bool, cpus: int, use_raster: bool):
    import networkx as nx

    if not use_raster:
        nx.set_node_attributes(G, {1: 10.0, 2: 20.0, 3: 30.0, 4: 40.0}, name="elevation")
        print("raster smoke disabled; assigned manual elevations")
        return G, "manual"

    try:
        import rasterio  # noqa: F401
    except ImportError as exc:
        nx.set_node_attributes(G, {1: 10.0, 2: 20.0, 3: 30.0, 4: 40.0}, name="elevation")
        print(f"rasterio unavailable ({exc}); assigned manual elevations instead")
        return G, "manual"

    raster_dir = output_dir / "rasters"
    full_path = raster_dir / "full.tif"
    left_path = raster_dir / "left.tif"
    right_path = raster_dir / "right.tif"

    # A single 2x2 raster covers all four nodes.
    write_raster(
        full_path,
        west=0.0,
        north=1.0,
        xsize=0.5,
        ysize=0.5,
        data=[[10.0, 20.0], [30.0, 40.0]],
    )

    if multi_raster:
        # Two adjacent rasters exercise the iterable-path / VRT code path.
        write_raster(
            left_path,
            west=0.0,
            north=1.0,
            xsize=0.5,
            ysize=0.5,
            data=[[11.0], [31.0]],
        )
        write_raster(
            right_path,
            west=0.5,
            north=1.0,
            xsize=0.5,
            ysize=0.5,
            data=[[21.0], [41.0]],
        )
        try:
            G = ox.elevation.add_node_elevations_raster(G, [left_path, right_path], cpus=cpus)
            return G, "multi-raster"
        except ImportError as exc:
            print(f"multi-raster elevation unavailable ({exc}); falling back to one raster")

    G = ox.elevation.add_node_elevations_raster(G, full_path, cpus=cpus)
    return G, "single-raster"


def validate_elevations(G) -> None:
    import networkx as nx

    elevations = dict(G.nodes(data="elevation"))
    if len(elevations) != G.number_of_nodes() or any(value is None for value in elevations.values()):
        raise RuntimeError("expected every node to have an elevation value")

    grades = nx.get_edge_attributes(G, "grade")
    if len(grades) != G.number_of_edges():
        raise RuntimeError("expected every edge to have a grade value")

    grades_abs = nx.get_edge_attributes(G, "grade_abs")
    if len(grades_abs) != G.number_of_edges():
        raise RuntimeError("expected every edge to have a grade_abs value")

    print(f"elevations attached to {len(elevations)} nodes")
    print(f"grades attached to {len(grades)} edges")


def run_plot_smoke(ox, G, output_dir: Path) -> str:
    if not getattr(ox.plot, "mpl_available", False):
        print("matplotlib unavailable; skipping plot smoke")
        return "skipped"

    try:
        import geopandas as gpd
        from shapely.geometry import Polygon
    except ImportError as exc:
        print(f"geopandas/shapely unavailable ({exc}); skipping plot smoke")
        return "skipped"

    output_dir.mkdir(parents=True, exist_ok=True)
    ox.settings.imgs_folder = output_dir

    route = [1, 2, 3, 4]
    reverse_route = list(reversed(route))

    # Exercise the default save location that is derived from settings.imgs_folder.
    ox.plot_graph(G, show=False, save=True, close=True)

    ox.plot_graph_route(
        G,
        route,
        show=False,
        save=True,
        close=True,
        filepath=output_dir / "route.png",
    )
    ox.plot_graph_routes(
        G,
        [route, reverse_route],
        route_colors=["r", "c"],
        route_linewidths=[4, 2],
        show=False,
        save=True,
        close=True,
        filepath=output_dir / "routes.png",
    )
    ox.plot_figure_ground(
        G,
        show=False,
        save=True,
        close=True,
        filepath=output_dir / "figure-ground.png",
    )

    footprints = gpd.GeoDataFrame(
        {"geometry": [Polygon([(0.05, 0.05), (0.95, 0.05), (0.95, 0.95), (0.05, 0.95)])]},
        crs=G.graph["crs"],
    )
    ox.plot_footprints(
        footprints,
        show=False,
        save=True,
        close=True,
        filepath=output_dir / "footprints.png",
    )

    print(f"plots written to {output_dir}")
    return "saved"


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    output_dir = args.output_dir or Path(tempfile.gettempdir()) / "osmnx-elevation-visualization-smoke"
    output_dir.mkdir(parents=True, exist_ok=True)

    if args.plot:
        try:
            import matplotlib as mpl
        except ImportError:
            pass
        else:
            mpl.use("Agg")

    try:
        import osmnx as ox
    except Exception as exc:  # pragma: no cover - depends on installation state
        raise SystemExit(f"osmnx must be importable in the execution environment: {exc}") from exc

    G = build_demo_graph()
    G, elevation_mode = attach_elevations(
        ox,
        G,
        output_dir,
        multi_raster=args.multi_raster,
        cpus=max(1, args.cpus),
        use_raster=args.raster,
    )
    G = ox.add_edge_grades(G, add_absolute=True)
    validate_elevations(G)

    plot_mode = "skipped"
    if args.plot:
        plot_mode = run_plot_smoke(ox, G, output_dir)

    print(f"smoke complete: elevation={elevation_mode}; plots={plot_mode}; output_dir={output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
