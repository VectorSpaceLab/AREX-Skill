#!/usr/bin/env python3
"""Run a tiny, process-local smoke for IR-SIM extension registries.

This helper intentionally does not create an environment or open a figure. It
registers unique in-memory individual/group behaviors, a kinematics handler,
and a grid generator, invokes each public dispatch path, then removes its
entries before exiting.
"""

from __future__ import annotations

import argparse
import os
from types import SimpleNamespace

# Keep imports below argument parsing and force safe plotting if a transitive
# import initializes Matplotlib.
os.environ.setdefault("MPLBACKEND", "Agg")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check process-local IR-SIM behavior and extension registries."
    )
    parser.add_argument(
        "--check",
        choices=("all", "behavior", "registries"),
        default="all",
        help="Run all checks, only behavior dispatch, or registry checks.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    import numpy as np

    from irsim.lib.behavior.behavior import Behavior
    from irsim.lib.behavior.behavior_registry import (
        behaviors_map,
        group_behaviors_map,
        register_behavior,
        register_group_behavior,
    )
    from irsim.lib.behavior.group_behavior import GroupBehavior
    from irsim.lib.handler.kinematics_handler import (
        KinematicsFactory,
        KinematicsHandler,
        _kinematics_registry,
        register_kinematics,
    )
    from irsim.world.map import build_grid_from_generator
    from irsim.world.map.grid_map_generator_base import GridMapGenerator

    tag = f"__disco_smoke_{os.getpid()}__"
    behavior_name = f"{tag}behavior"
    group_name = f"{tag}group"
    kinematics_name = f"{tag}kinematics"
    map_name = f"{tag}map"
    observed: dict[str, object] = {}

    @register_behavior("diff", behavior_name)
    def smoke_behavior(ego_object, external_objects, **kwargs):
        observed["ego"] = ego_object
        observed["external"] = external_objects
        return np.array([[float(kwargs["gain"])], [0.0]])

    @register_group_behavior("omni", group_name)
    def smoke_group_behavior(members, **kwargs):
        observed["members"] = members
        return [np.full((2, 1), float(kwargs["gain"])) for _ in members]

    @register_kinematics(kinematics_name)
    class SmokeKinematics(KinematicsHandler):
        action_dim = 2
        min_state_dim = 3
        state_dim = 3

        def step(self, state, velocity, step_time):
            return state.copy()

    class SmokeMapGenerator(GridMapGenerator):
        name = map_name
        yaml_param_names = ("marker",)

        def __init__(self, width, height, marker=100, **kwargs):
            super().__init__()
            self.width = width
            self.height = height
            self.marker = marker

        def _build_grid(self):
            return np.full((self.width, self.height), self.marker)

    try:
        if args.check in ("all", "behavior"):
            info = SimpleNamespace(kinematics="diff", name="smoke")
            ego = SimpleNamespace(role="robot")
            external = [SimpleNamespace(role="robot")]
            facade = Behavior(
                object_info=info,
                behavior_dict={"name": behavior_name, "gain": 0.25},
            )
            action = facade.gen_vel(ego_object=ego, external_objects=external)
            assert action.shape == (2, 1)
            assert float(action[0, 0]) == 0.25
            assert observed["ego"] is ego
            assert observed["external"] == external

            members = [
                SimpleNamespace(kinematics="omni"),
                SimpleNamespace(kinematics="omni"),
            ]
            group = GroupBehavior(members, name=group_name, gain=0.5)
            actions = group.gen_group_vel()
            assert len(actions) == len(members)
            assert all(item.shape == (2, 1) for item in actions)
            assert all(float(item[0, 0]) == 0.5 for item in actions)
            assert observed["members"] == members

        if args.check in ("all", "registries"):
            handler = KinematicsFactory.create_kinematics(name=kinematics_name)
            assert isinstance(handler, SmokeKinematics)
            assert KinematicsFactory.get_handler_class(kinematics_name) is SmokeKinematics

            grid = build_grid_from_generator(
                {"name": map_name, "resolution": 1.0, "marker": 100},
                world_width=2.0,
                world_height=3.0,
            )
            assert grid.shape == (2, 3)
            assert grid.dtype == np.float64
            assert np.all(grid == 100.0)

        print(f"custom_behavior_smoke: PASS ({args.check})")
        return 0
    finally:
        behaviors_map.pop(("diff", behavior_name), None)
        group_behaviors_map.pop(("omni", group_name), None)
        _kinematics_registry.pop(kinematics_name.lower(), None)
        GridMapGenerator.registry.pop(map_name, None)


if __name__ == "__main__":
    raise SystemExit(main())
