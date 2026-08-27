#!/usr/bin/env python3
"""Smoke-test Mesa discrete and experimental continuous space APIs."""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
import warnings
from collections.abc import Callable

import numpy as np
import mesa
from mesa import Model
from mesa.discrete_space import (
    Cell,
    CellAgent,
    CellCollection,
    FixedAgent,
    Grid2DMovingAgent,
    HexGrid,
    Network,
    OrthogonalMooreGrid,
    OrthogonalVonNeumannGrid,
    VoronoiGrid,
)
from mesa.experimental.continuous_space import ContinuousSpace, ContinuousSpaceAgent


def ensure(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def expect_raises(exc_type: type[BaseException], func: Callable[[], object], label: str) -> bool:
    try:
        func()
    except exc_type:
        return True
    except Exception as exc:  # pragma: no cover - defensive smoke guard
        raise RuntimeError(
            f"{label}: expected {exc_type.__name__}, got {type(exc).__name__}: {exc}"
        ) from exc
    raise RuntimeError(f"{label}: expected {exc_type.__name__}")


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Smoke-test Mesa discrete and continuous space APIs.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--seed", type=int, default=42, help="Seed passed to mesa.Model(rng=...).")
    parser.add_argument(
        "--size",
        type=int,
        default=4,
        help="Base side length for the small grids used in the smoke check.",
    )
    parser.add_argument(
        "--json-indent",
        type=int,
        default=2,
        help="JSON indentation level for the final report.",
    )
    parser.add_argument(
        "--skip-network",
        action="store_true",
        help="Skip the optional Network smoke when networkx is available.",
    )
    args = parser.parse_args(argv)

    if args.size < 2:
        parser.error("--size must be >= 2")

    return args


def build_discrete_report(seed: int, size: int) -> dict[str, object]:
    model = Model(rng=seed)
    rng = model.random

    grid = OrthogonalMooreGrid((size, size), torus=False, capacity=2, random=rng)

    sugar = grid.create_property_layer("sugar", default_value=1.0)
    grid.add_property_layer("moisture", np.zeros((size, size), dtype=float))
    grid.create_property_layer("protected", default_value=5.0, read_only=True)

    ensure(grid.property_layers["sugar"].shape == (size, size), "sugar layer shape mismatch")
    ensure(grid.property_layers["moisture"].shape == (size, size), "moisture layer shape mismatch")
    ensure(sorted(grid.property_layers) == ["empty", "moisture", "protected", "sugar"], "unexpected grid property layers")

    sugar[0, 0] += 1.0
    grid[0, 0].sugar += 2.0
    ensure(np.isclose(grid[0, 0].sugar, 4.0), "property-layer accessor is not linked to the backing array")

    name_conflict_error = expect_raises(
        ValueError,
        lambda: grid.create_property_layer("width"),
        "property layer name conflict",
    )
    shape_error = expect_raises(
        ValueError,
        lambda: grid.add_property_layer("bad", np.zeros((2, 2), dtype=float)),
        "property layer shape mismatch",
    )
    read_only_error = expect_raises(
        AttributeError,
        lambda: setattr(grid[0, 0], "protected", 9.0),
        "read-only property layer assignment",
    )

    cell = grid[0, 0]
    agent_a = CellAgent(model)
    agent_b = CellAgent(model)

    agent_a.move_to(cell)
    ensure(cell in grid.cells_with_capacity, "partially filled cell should still be available")
    ensure(cell not in grid.empties, "occupied cell should not be empty")
    ensure(grid.select_random_empty_cell().empty, "select_random_empty_cell returned a non-empty cell")

    agent_b.move_to(cell)
    ensure(cell not in grid.cells_with_capacity, "full cell should not be available")
    ensure(not grid.select_random_cell_with_capacity().is_full, "selected cell with capacity is full")

    row = grid.all_cells.select(lambda c: c.coordinate[0] == 0, at_most=2)
    row_pick = row.select_random_cell()
    ensure(row_pick in row, "selected cell is not a member of the filtered CellCollection")

    occupied_collection = CellCollection([cell], random=rng)
    picked_agent = occupied_collection.select_random_agent()
    ensure(picked_agent in cell.agents, "selected agent is not a member of the occupied collection")

    capacity_before_remove = len(list(grid.cells_with_capacity))
    empties_before_remove = len(grid.empties)
    agent_a.remove()
    agent_b.remove()
    ensure(cell in grid.empties, "cell should become empty again after removing agents")
    ensure(cell in grid.cells_with_capacity, "vacated cell should become available again")

    fixed_cell = Cell((99,), random=rng)
    fixed_agent = FixedAgent(model)
    fixed_agent.cell = fixed_cell
    fixed_reassignment_error = expect_raises(
        ValueError,
        lambda: setattr(fixed_agent, "cell", Cell((100,), random=rng)),
        "FixedAgent reassignment",
    )
    fixed_agent.remove()
    ensure(fixed_agent.cell is None, "FixedAgent.remove() did not clear the cell reference")
    ensure(fixed_agent not in model.agents, "FixedAgent.remove() did not deregister the agent")

    mover = Grid2DMovingAgent(model)
    mover.cell = grid[1, 1]
    mover.move("north")
    ensure(mover.cell.coordinate == (0, 1), "Grid2DMovingAgent.move('north') did not move one step")

    von = OrthogonalVonNeumannGrid((size, size), torus=False, random=rng)
    diagonal_mover = Grid2DMovingAgent(model)
    diagonal_mover.cell = von[1, 1]
    diagonal_move_error = expect_raises(
        ValueError,
        lambda: diagonal_mover.move("upright"),
        "Grid2DMovingAgent diagonal move on Von Neumann grid",
    )

    hex_size = size if size % 2 == 0 else size + 1
    hexgrid = HexGrid((hex_size, hex_size), torus=True, random=rng)
    wrapped_hex = hexgrid.find_nearest_cell(np.array([-0.1, 0.0]))
    reference_hex = hexgrid.find_nearest_cell(np.array([hex_size * np.sqrt(3.0) - 0.1, 0.0]))
    ensure(wrapped_hex == reference_hex, "HexGrid torus wrapping did not land on the same cell")

    voronoi_points = [
        [0.0, 0.0],
        [1.0, 0.0],
        [0.5, 1.0],
        [1.5, 1.0],
        [0.0, 2.0],
        [1.0, 2.0],
    ]
    voronoi = VoronoiGrid(voronoi_points, capacity=lambda area: max(1, int(round(area * 10))), random=rng)
    voronoi_cell = voronoi.find_nearest_cell(np.array([0.5, 1.0]))
    ensure("polygon" in voronoi_cell.properties, "Voronoi cell is missing polygon metadata")
    ensure("area" in voronoi_cell.properties, "Voronoi cell is missing area metadata")
    ensure(voronoi_cell.capacity is not None and voronoi_cell.capacity >= 1, "Voronoi callable capacity was not applied")

    return {
        "grid": {
            "dimensions": [size, size],
            "property_layers": sorted(grid.property_layers),
            "capacity_before_remove": int(capacity_before_remove),
            "empties_before_remove": int(empties_before_remove),
            "cell_available_after_fill": bool(cell not in grid.cells_with_capacity),
            "cell_empty_after_remove": bool(cell in grid.empties),
            "cell_available_after_remove": bool(cell in grid.cells_with_capacity),
            "name_conflict_error": bool(name_conflict_error),
            "shape_error": bool(shape_error),
            "read_only_error": bool(read_only_error),
        },
        "cell_collection": {
            "row_size": int(len(row)),
            "selected_cell_coordinate": list(row_pick.coordinate),
            "selected_agent_type": type(picked_agent).__name__,
        },
        "agents": {
            "fixed_reassignment_error": bool(fixed_reassignment_error),
            "diagonal_move_error": bool(diagonal_move_error),
        },
        "hex": {
            "size": [hex_size, hex_size],
            "torus_wrap_match": bool(wrapped_hex == reference_hex),
        },
        "voronoi": {
            "cell_count": int(len(voronoi._cells)),
            "nearest_coordinate": int(voronoi_cell.coordinate),
            "has_polygon": bool("polygon" in voronoi_cell.properties),
            "has_area": bool("area" in voronoi_cell.properties),
        },
    }


def build_network_report(seed: int, skip_network: bool) -> dict[str, object]:
    if skip_network or importlib.util.find_spec("networkx") is None:
        return {"available": False, "status": "skipped"}

    import networkx as nx  # noqa: PLC0415

    model = Model(rng=seed)
    rng = model.random

    graph = nx.path_graph(3)
    layout = {node: (float(node), 0.0) for node in graph.nodes}
    network = Network(graph, layout=layout, random=rng)

    nearest = network.find_nearest_cell(np.array([1.1, 0.0]))
    ensure(nearest.coordinate == 1, "Network nearest-cell lookup returned the wrong node")

    new_cell = Cell(coordinate=99, position=np.array([9.0, 0.0]), random=rng)
    network.add_cell(new_cell)
    ensure(network._kdtree_dirty is True, "Network KD-tree should be marked dirty after adding a spatial cell")

    dirty_rebuild_target = network.find_nearest_cell(np.array([8.9, 0.0]))
    ensure(dirty_rebuild_target.coordinate == 99, "Network did not rebuild its KD-tree lazily")
    ensure(network._kdtree_dirty is False, "Network KD-tree should be clean after a spatial query")

    network.remove_cell(new_cell)
    after_remove = network.find_nearest_cell(np.array([1.1, 0.0]))
    ensure(after_remove.coordinate == 1, "Network lookup after removal returned the wrong node")

    return {
        "available": True,
        "node_count": int(len(network._cells)),
        "nearest_coordinate": int(nearest.coordinate),
        "dirty_rebuild_target": int(dirty_rebuild_target.coordinate),
        "dirty_rebuild_flag_cleared": bool(network._kdtree_dirty is False),
        "after_remove_coordinate": int(after_remove.coordinate),
    }


def build_continuous_report(seed: int) -> dict[str, object]:
    model = Model(rng=seed)
    space = ContinuousSpace(np.array([[0.0, 1.0], [0.0, 1.0]]), torus=True, random=model.random)

    a1 = ContinuousSpaceAgent(space, model)
    a2 = ContinuousSpaceAgent(space, model)
    a3 = ContinuousSpaceAgent(space, model)

    a1.position = np.array([0.1, 0.1])
    a2.position = np.array([0.9, 0.1])
    a3.position = np.array([0.5, 0.5])

    ensure(space.ndims == 2, "continuous space should report two dimensions")
    ensure(np.allclose(space.size, [1.0, 1.0]), "continuous space size mismatch")
    ensure(np.allclose(space.center, [0.5, 0.5]), "continuous space center mismatch")
    ensure(space.in_bounds([0.5, 0.5]), "point inside the space should be in bounds")
    ensure(not space.in_bounds([1.2, 0.5]), "point outside the non-wrapped bounds should be out of bounds")
    ensure(np.allclose(space.torus_correct([1.2, -0.1]), [0.2, 0.9]), "torus correction did not wrap as expected")

    neighbors, distances = a1.get_neighbors_in_radius(0.3)
    ensure(len(neighbors) == 1 and neighbors[0] is a2, "radius query should return the nearest neighbor only")
    ensure(np.allclose(distances, [0.2]), "radius query distance mismatch")

    nearest, nearest_distances = a1.get_nearest_neighbors(k=1)
    ensure(len(nearest) == 1 and nearest[0] is a2, "nearest-neighbor query should return the closest other agent")
    ensure(np.allclose(nearest_distances, [0.2]), "nearest-neighbor distance mismatch")

    a4 = ContinuousSpaceAgent(space, model)
    a4.position = np.array([1.8, 1.8])
    ensure(np.allclose(a4.position, [0.8, 0.8]), "torus wrapping did not update the agent position")

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        many_agents, many_distances = space.get_k_nearest_agents(np.array([0.1, 0.1]), k=10)
    ensure(len(caught) >= 1, "k larger than the population should emit a warning")
    ensure(len(many_agents) == 4, "k larger than the population should still return every agent")
    ensure(len(many_distances) == 4, "k larger than the population should still return every distance")

    empty_space = ContinuousSpace(np.array([[0.0, 1.0], [0.0, 1.0]]), torus=False, random=model.random)
    empty_agents, empty_distances = empty_space.get_k_nearest_agents(np.array([0.0, 0.0]), k=1)
    zero_agents, zero_distances = empty_space.get_k_nearest_agents(np.array([0.0, 0.0]), k=0)
    ensure(empty_agents == [] and len(empty_distances) == 0, "empty space should return no agents")
    ensure(zero_agents == [] and len(zero_distances) == 0, "k=0 should return no agents")

    before_remove = len(space.active_agents)
    a3.remove()
    ensure(len(space.active_agents) == before_remove - 1, "removing a continuous agent did not shrink the active list")
    ensure(a3.space is None, "removed continuous agent should drop its space reference")

    return {
        "dimensions": [[0.0, 1.0], [0.0, 1.0]],
        "active_agents": int(len(space.active_agents)),
        "agent_positions_shape": list(space.agent_positions.shape),
        "nearest_neighbor": type(nearest[0]).__name__,
        "nearest_distance": float(nearest_distances[0]),
        "radius_neighbor_count": int(len(neighbors)),
        "wrapped_position": [float(v) for v in a4.position.tolist()],
        "warning_count": int(len(caught)),
        "empty_k_count": int(len(empty_agents)),
        "zero_k_count": int(len(zero_agents)),
        "removed_agent_cleared_space": bool(a3.space is None),
    }


def main(argv: list[str] | None = None) -> int:
    if sys.version_info < (3, 12):
        raise SystemExit("Python 3.12 or newer is required.")

    args = parse_args(sys.argv[1:] if argv is None else argv)

    payload = {
        "mesa_version": getattr(mesa, "__version__", "unknown"),
        "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        "seed": int(args.seed),
        "size": int(args.size),
        "discrete": build_discrete_report(args.seed, args.size),
        "network": build_network_report(args.seed, args.skip_network),
        "continuous": build_continuous_report(args.seed),
    }

    print(json.dumps(payload, indent=args.json_indent, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
