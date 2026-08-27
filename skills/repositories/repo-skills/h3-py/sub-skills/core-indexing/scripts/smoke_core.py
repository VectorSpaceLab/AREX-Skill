#!/usr/bin/env python3
"""Small, deterministic smoke checks for the public h3 string API."""

from __future__ import annotations

import argparse


CELL = "8928308280fffff"
LAT = 37.7752702151959
LNG = -122.418307270836


def check() -> None:
    """Run tiny assertions that exercise the core route."""
    import h3

    cell = h3.latlng_to_cell(LAT, LNG, 9)
    assert cell == CELL, cell
    assert h3.is_valid_index(cell)
    assert h3.is_valid_cell(cell)
    assert h3.get_resolution(cell) == 9
    assert len(h3.cell_to_latlng(cell)) == 2
    assert len(h3.cell_to_boundary(cell)) == 6

    parent = h3.cell_to_parent(cell, 8)
    children = h3.cell_to_children(parent, 9)
    assert cell in children
    assert len(children) == h3.cell_to_children_size(parent, 9)

    ring = h3.grid_ring(cell, 1)
    assert len(ring) == 6
    assert all(h3.grid_distance(cell, neighbor) == 1 for neighbor in ring)

    edge = h3.cells_to_directed_edge(cell, ring[0])
    assert h3.is_valid_index(edge)
    assert h3.directed_edge_to_cells(edge) == (cell, ring[0])

    vertex = h3.cell_to_vertexes(cell)[0]
    assert h3.is_valid_vertex(vertex)
    assert len(h3.vertex_to_latlng(vertex)) == 2

    i, j = h3.cell_to_local_ij(cell, ring[0])
    assert h3.local_ij_to_cell(cell, i, j) == ring[0]
    assert h3.cell_area(cell) > 0
    assert h3.edge_length(edge, unit="m") > 0
    assert h3.great_circle_distance((0, 0), (1, 1), unit="km") > 0


def point() -> None:
    """Print one stable point-to-cell result."""
    import h3

    print(h3.latlng_to_cell(LAT, LNG, 9))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "action",
        nargs="?",
        choices=("check", "point"),
        default="check",
        help="run assertions (default) or print the example cell",
    )
    args = parser.parse_args()
    if args.action == "point":
        point()
    else:
        check()
        print("core smoke checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
