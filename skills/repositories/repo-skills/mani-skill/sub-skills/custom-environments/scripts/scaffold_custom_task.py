#!/usr/bin/env python3
"""Emit or validate a minimal ManiSkill custom-task scaffold.

This helper is self-contained: it only writes bundled template text and validates
local scaffold files with lightweight structural checks.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from string import Template
from textwrap import dedent

TASK_TEMPLATE = Template(
    dedent(
        '''
        from __future__ import annotations

        from typing import Any, Union

        import numpy as np
        import sapien
        import torch

        from mani_skill.agents.robots import Fetch, Panda
        from mani_skill.envs.sapien_env import BaseEnv
        from mani_skill.sensors.camera import CameraConfig
        from mani_skill.utils import sapien_utils
        from mani_skill.utils.building import actors
        from mani_skill.utils.registration import register_env
        from mani_skill.utils.scene_builder.table import TableSceneBuilder
        from mani_skill.utils.structs import Pose
        from mani_skill.utils.structs.types import GPUMemoryConfig, SimConfig


        @register_env("$env_id", max_episode_steps=$max_episode_steps)
        class $class_name(BaseEnv):
            """Starter tabletop task scaffold."""

            # Replace the robot list and type annotation if you use a different embodiment.
            SUPPORTED_ROBOTS = [$supported_robots]
            agent: Union[Panda, Fetch]

            goal_radius = 0.1
            cube_half_size = 0.02

            def __init__(self, *args, robot_uids="$default_robot_uid", robot_init_qpos_noise=0.02, **kwargs):
                self.robot_init_qpos_noise = robot_init_qpos_noise
                self.goal_pos = None
                super().__init__(*args, robot_uids=robot_uids, **kwargs)

            @property
            def _default_sim_config(self):
                return SimConfig(
                    gpu_memory_config=GPUMemoryConfig(
                        found_lost_pairs_capacity=2**25,
                        max_rigid_patch_count=2**18,
                    )
                )

            @property
            def _default_sensor_configs(self):
                pose = sapien_utils.look_at(eye=[0.3, 0, 0.6], target=[-0.1, 0, 0.1])
                return [
                    CameraConfig(
                        "base_camera",
                        pose=pose,
                        width=128,
                        height=128,
                        fov=np.pi / 2,
                        near=0.01,
                        far=100,
                    )
                ]

            @property
            def _default_human_render_camera_configs(self):
                pose = sapien_utils.look_at([0.6, 0.7, 0.6], [0.0, 0.0, 0.35])
                return [
                    CameraConfig(
                        "render_camera",
                        pose=pose,
                        width=512,
                        height=512,
                        fov=1,
                        near=0.01,
                        far=100,
                    )
                ]

            def _load_agent(self, options: dict):
                super()._load_agent(options, sapien.Pose(p=[-0.615, 0, 0]))

            def _load_scene(self, options: dict):
                self.table_scene = TableSceneBuilder(
                    env=self,
                    robot_init_qpos_noise=self.robot_init_qpos_noise,
                )
                self.table_scene.build()

                builder = self.scene.create_actor_builder()
                builder.add_box_collision(half_size=[self.cube_half_size] * 3)
                builder.add_box_visual(
                    half_size=[self.cube_half_size] * 3,
                    material=sapien.render.RenderMaterial(
                        base_color=np.array([12, 42, 160, 255]) / 255,
                    ),
                )
                builder.initial_pose = sapien.Pose(p=[0, 0, self.cube_half_size])
                self.obj = builder.build(name="cube")

                self.goal_site = actors.build_red_white_target(
                    self.scene,
                    radius=self.goal_radius,
                    thickness=1e-5,
                    name="goal_site",
                    add_collision=False,
                    body_type="kinematic",
                    initial_pose=sapien.Pose(p=[0, 0, 1e-3]),
                )
                self._hidden_objects.append(self.goal_site)

            def _initialize_episode(self, env_idx: torch.Tensor, options: dict):
                with torch.device(self.device):
                    b = len(env_idx)
                    self.table_scene.initialize(env_idx)

                    xyz = torch.zeros((b, 3), device=self.device)
                    xyz[..., :2] = torch.rand((b, 2), device=self.device) * 0.2 - 0.1
                    xyz[..., 2] = self.cube_half_size
                    self.obj.set_pose(Pose.create_from_pq(p=xyz, q=[1, 0, 0, 0]))

                    goal_xyz = xyz + torch.tensor([0.12, 0.0, 0.0], device=self.device)
                    goal_xyz[..., 2] = 1e-3
                    self.goal_pos = goal_xyz
                    self.goal_site.set_pose(Pose.create_from_pq(p=goal_xyz, q=[1, 0, 0, 0]))

            def evaluate(self):
                is_obj_placed = (
                    torch.linalg.norm(self.obj.pose.p[..., :2] - self.goal_pos[..., :2], axis=1)
                    < self.goal_radius
                )
                is_obj_stable = self.obj.pose.p[..., 2] > self.cube_half_size / 2
                fail = self.obj.pose.p[..., 2] < 0.0
                return {
                    "success": is_obj_placed & is_obj_stable,
                    "fail": fail,
                    "is_obj_placed": is_obj_placed,
                }

            def _get_obs_extra(self, info: dict):
                obs = dict(
                    tcp_pose=self.agent.tcp.pose.raw_pose,
                    goal_pos=self.goal_pos,
                )
                if self.obs_mode_struct.use_state:
                    obs.update(
                        obj_pose=self.obj.pose.raw_pose,
                        obj_to_goal_pos=self.goal_pos - self.obj.pose.p,
                    )
                return obs

            def compute_dense_reward(self, obs: Any, action: torch.Tensor, info: dict):
                tcp_to_obj_dist = torch.linalg.norm(
                    self.obj.pose.p - self.agent.tcp.pose.p, axis=1
                )
                reaching_reward = 1 - torch.tanh(5 * tcp_to_obj_dist)
                obj_to_goal_dist = torch.linalg.norm(
                    self.goal_pos[..., :2] - self.obj.pose.p[..., :2], axis=1
                )
                place_reward = 1 - torch.tanh(5 * obj_to_goal_dist)
                reward = reaching_reward + place_reward * (tcp_to_obj_dist < 0.01)
                reward[info["success"]] = 4.0
                return reward

            def compute_normalized_dense_reward(self, obs: Any, action: torch.Tensor, info: dict):
                return self.compute_dense_reward(obs, action, info) / 4.0

            def get_state_dict(self):
                state = super().get_state_dict()
                state["goal_pos"] = self.goal_pos.clone()
                return state

            def set_state_dict(self, state, env_idx: torch.Tensor = None):
                super().set_state_dict(state, env_idx)
                self.goal_pos = state["goal_pos"].clone()
                self.goal_site.set_pose(Pose.create_from_pq(p=self.goal_pos, q=[1, 0, 0, 0]))
        '''
    )
)

SCENE_BUILDER_TEMPLATE = Template(
    dedent(
        '''
        from __future__ import annotations

        import torch

        from mani_skill.utils.scene_builder.scene_builder import SceneBuilder


        class $scene_builder_name(SceneBuilder):
            """Reusable layout scaffold.

            Put one-time build work in build() and reset-time work in initialize().
            Add register_scene_builder if you want to expose this by uid.
            """

            builds_lighting = False
            build_configs = None
            init_configs = None

            def build(self, build_config_idxs=None):
                # Construct shared static geometry, props, or caches here.
                return self

            def initialize(self, env_idx: torch.Tensor, init_config_idxs=None):
                # Reset layout-specific state for the selected envs here.
                return self
        '''
    )
)

TASK_PATTERNS = [
    ("register_env", r"@register_env\("),
    ("base_env", r"class\s+\w+\(BaseEnv\):"),
    ("supported_robots", r"SUPPORTED_ROBOTS\s*=\s*\[.*\]"),
    ("load_agent", r"def _load_agent\("),
    ("load_scene", r"def _load_scene\("),
    ("initialize_episode", r"def _initialize_episode\("),
    ("table_scene", r"TableSceneBuilder\("),
    ("camera_config", r"CameraConfig\("),
    ("pose_broadcast", r"Pose\.create_from_pq\("),
    ("evaluate", r"def evaluate\("),
    ("success_key", r'"success"'),
    ("fail_key", r'"fail"'),
    ("get_obs_extra", r"def _get_obs_extra\("),
    ("dense_reward", r"def compute_dense_reward\("),
    ("normalized_reward", r"def compute_normalized_dense_reward\("),
    ("get_state_dict", r"def get_state_dict\("),
    ("set_state_dict", r"def set_state_dict\("),
    ("goal_state", r"goal_pos"),
    ("batched_reset", r"len\(env_idx\)"),
]

SCENE_PATTERNS = [
    ("scene_class", r"class\s+\w+\(SceneBuilder\):"),
    ("build", r"def build\("),
    ("initialize", r"def initialize\("),
]


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    emit = sub.add_parser("emit", help="Write a scaffold to a destination directory")
    emit.add_argument("--out", required=True, type=Path, help="Output directory")
    emit.add_argument("--env-id", default="CustomEnv-v1", help="gym env id")
    emit.add_argument("--class-name", default="CustomEnv", help="Python class name")
    emit.add_argument(
        "--scene-builder-name",
        default="ExampleSceneBuilder",
        help="Python scene builder class name",
    )
    emit.add_argument(
        "--supported-robots",
        default="panda,fetch",
        help="Comma-separated robot uids for SUPPORTED_ROBOTS",
    )
    emit.add_argument(
        "--default-robot-uid",
        default="panda",
        help="Default robot_uids value for __init__",
    )
    emit.add_argument(
        "--max-episode-steps",
        default=50,
        type=int,
        help="Environment time limit",
    )
    emit.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing scaffold files",
    )

    validate = sub.add_parser("validate", help="Check an emitted scaffold")
    validate.add_argument("--path", required=True, type=Path, help="Scaffold directory or task file")

    return parser.parse_args(argv)


def render_list(raw: str) -> str:
    items = [item.strip() for item in raw.split(",") if item.strip()]
    if not items:
        raise ValueError("supported robot list cannot be empty")
    return ", ".join(f'\"{item}\"' for item in items)


def write_file(path: Path, content: str, overwrite: bool) -> None:
    if path.exists() and not overwrite:
        raise FileExistsError(f"{path} already exists; pass --overwrite to replace it")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def emit(args: argparse.Namespace) -> int:
    out = args.out
    out.mkdir(parents=True, exist_ok=True)

    context = {
        "env_id": args.env_id,
        "class_name": args.class_name,
        "scene_builder_name": args.scene_builder_name,
        "supported_robots": render_list(args.supported_robots),
        "default_robot_uid": args.default_robot_uid,
        "max_episode_steps": args.max_episode_steps,
    }

    task_path = out / "task.py"
    scene_builder_path = out / "scene_builder.py"
    write_file(task_path, TASK_TEMPLATE.substitute(context), args.overwrite)
    write_file(
        scene_builder_path,
        SCENE_BUILDER_TEMPLATE.substitute(context),
        args.overwrite,
    )
    print(f"wrote {task_path}")
    print(f"wrote {scene_builder_path}")
    return 0


def _validate_text(text: str, patterns: list[tuple[str, str]]) -> list[str]:
    missing = []
    for label, pattern in patterns:
        if not re.search(pattern, text, flags=re.M | re.S):
            missing.append(label)
    return missing


def validate(args: argparse.Namespace) -> int:
    base = args.path
    if base.is_file():
        task_path = base
        scene_builder_path = base.with_name("scene_builder.py")
    else:
        task_path = base / "task.py"
        scene_builder_path = base / "scene_builder.py"

    errors = []
    if not task_path.exists():
        errors.append(f"missing task scaffold: {task_path}")
    else:
        missing = _validate_text(task_path.read_text(encoding="utf-8"), TASK_PATTERNS)
        if missing:
            errors.append(f"task.py missing patterns: {', '.join(missing)}")

    if not scene_builder_path.exists():
        errors.append(f"missing scene builder scaffold: {scene_builder_path}")
    else:
        missing = _validate_text(
            scene_builder_path.read_text(encoding="utf-8"), SCENE_PATTERNS
        )
        if missing:
            errors.append(f"scene_builder.py missing patterns: {', '.join(missing)}")

    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1

    print(f"validated scaffold at {base}")
    return 0


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    if args.command == "emit":
        return emit(args)
    if args.command == "validate":
        return validate(args)
    raise AssertionError(f"unhandled command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
