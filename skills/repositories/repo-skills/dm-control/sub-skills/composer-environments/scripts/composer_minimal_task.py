#!/usr/bin/env python3
"""Minimal installed-package Composer entity/task/environment smoke demo.

This script defines a small articulated Composer entity, wraps it in a task,
creates a composer.Environment, prints specs and qualified observation keys, and
runs a short rollout. It does not read dm_control source files and does not
render frames.
"""

import argparse
import collections
import warnings

# The demo does not render. Some headless hosts emit this non-fatal GLFW warning
# while importing dm_control internals; suppress it so CPU smoke output is clear.
warnings.filterwarnings(
    "ignore", message=r".*DISPLAY environment variable is missing.*"
)

import numpy as np

from dm_control import composer, mjcf
from dm_control.composer.observation import observable


class HingeEntity(composer.Entity):
    """A tiny one-joint entity with entity-scoped observables."""

    def _build(self, name="demo_hinge"):
        self._mjcf_root = mjcf.RootElement(model=name)
        body = self._mjcf_root.worldbody.add(
            "body", name="link", pos=[0.0, 0.0, 0.4]
        )
        body.add(
            "geom",
            name="capsule",
            type="capsule",
            fromto=[0.0, 0.0, 0.0, 0.0, 0.0, -0.3],
            size=[0.03],
            rgba=[0.2, 0.4, 0.8, 1.0],
        )
        self._joint = body.add(
            "joint",
            name="hinge",
            type="hinge",
            axis=[0.0, 1.0, 0.0],
            limited=True,
            range=[-1.0, 1.0],
            damping=0.1,
        )
        self._actuator = self._mjcf_root.actuator.add(
            "position",
            name="hinge_target",
            joint=self._joint,
            kp=8.0,
            ctrllimited=True,
            ctrlrange=[-1.0, 1.0],
        )

    @property
    def mjcf_model(self):
        return self._mjcf_root

    @property
    def joint(self):
        return self._joint

    @property
    def actuator(self):
        return self._actuator

    def _build_observables(self):
        return HingeObservables(self)


class HingeObservables(composer.Observables):
    """Entity observables declared with @composer.observable."""

    def __init__(self, entity):
        super().__init__(entity)
        self.enable_all()

    @composer.observable
    def hinge_position(self):
        # A delayed two-sample buffer demonstrates observation buffering.
        return observable.MJCFFeature(
            "qpos", self._entity.joint, buffer_size=2, delay=1
        )

    @composer.observable
    def hinge_velocity_mean(self):
        # Aggregating over a two-sample buffer demonstrates aggregator behavior.
        return observable.MJCFFeature(
            "qvel", self._entity.joint, buffer_size=2, aggregator="mean"
        )


class DemoWorld(composer.Entity):
    """Root entity that attaches the hinge entity to produce qualified keys."""

    def _build(self, name="demo_world"):
        self._mjcf_root = mjcf.RootElement(model=name)
        self._hinge = HingeEntity(name="demo_hinge")
        self.attach(self._hinge)

    @property
    def mjcf_model(self):
        return self._mjcf_root

    @property
    def hinge(self):
        return self._hinge


class DemoTask(composer.Task):
    """Minimal task with hooks, task observables, reward, and timing."""

    def __init__(self):
        self._root_entity = DemoWorld()
        self.hook_counts = collections.Counter()

        task_time = observable.Generic(
            lambda physics: np.array([physics.time()], dtype=np.float64)
        )
        task_time.enabled = True
        self._task_observables = collections.OrderedDict([("task_time", task_time)])

        # Four MuJoCo physics steps per agent control step.
        self.set_timesteps(control_timestep=0.02, physics_timestep=0.005)

    @property
    def root_entity(self):
        return self._root_entity

    @property
    def task_observables(self):
        return self._task_observables

    def initialize_episode_mjcf(self, random_state):
        del random_state
        self.hook_counts["initialize_episode_mjcf"] += 1

    def after_compile(self, physics, random_state):
        del physics, random_state
        self.hook_counts["after_compile"] += 1

    def initialize_episode(self, physics, random_state):
        self.hook_counts["initialize_episode"] += 1
        physics.bind(self.root_entity.hinge.joint).qpos = random_state.uniform(
            low=-0.05, high=0.05, size=1
        )

    def before_step(self, physics, action, random_state):
        self.hook_counts["before_step"] += 1
        # The base Task implementation writes the action into MuJoCo controls.
        super().before_step(physics, action, random_state)

    def before_substep(self, physics, action, random_state):
        del physics, action, random_state
        self.hook_counts["before_substep"] += 1

    def after_substep(self, physics, random_state):
        del physics, random_state
        self.hook_counts["after_substep"] += 1

    def after_step(self, physics, random_state):
        del physics, random_state
        self.hook_counts["after_step"] += 1

    def get_reward(self, physics):
        qpos = physics.bind(self.root_entity.hinge.joint).qpos[0]
        return float(1.0 - abs(qpos))


def _describe_spec(name, spec):
    pieces = [f"shape={spec.shape}", f"dtype={np.dtype(spec.dtype).name}"]
    if getattr(spec, "name", None):
        pieces.append(f"name={spec.name!r}")
    if hasattr(spec, "minimum") and hasattr(spec, "maximum"):
        pieces.append(f"min={np.asarray(spec.minimum).tolist()}")
        pieces.append(f"max={np.asarray(spec.maximum).tolist()}")
    return f"{name}: " + ", ".join(pieces)


def _step_type_name(time_step):
    return getattr(time_step.step_type, "name", str(time_step.step_type))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--steps", type=int, default=5, help="Number of steps to run.")
    parser.add_argument("--seed", type=int, default=7, help="Environment RNG seed.")
    args = parser.parse_args()

    task = DemoTask()
    env = composer.Environment(
        task,
        random_state=args.seed,
        max_reset_attempts=2,
        strip_singleton_obs_buffer_dim=True,
        delayed_observation_padding=composer.ObservationPadding.ZERO,
    )

    try:
        time_step = env.reset()

        print("action_spec:")
        print("  " + _describe_spec("action", env.action_spec()))
        print("observation_spec:")
        for key, spec in env.observation_spec().items():
            print("  " + _describe_spec(key, spec))
        print("reset_observation_keys:", list(time_step.observation.keys()))
        print("control_timestep:", env.control_timestep())
        print(
            "physics_steps_per_control_step:",
            task.physics_steps_per_control_step,
        )

        action_spec = env.action_spec()
        action = np.zeros(action_spec.shape, dtype=action_spec.dtype)
        for step_index in range(args.steps):
            time_step = env.step(action)
            print(
                f"step {step_index + 1}: "
                f"step_type={_step_type_name(time_step)} "
                f"reward={time_step.reward:.6f} "
                f"discount={time_step.discount} "
                f"sim_time={env.physics.time():.3f}"
            )
            if time_step.last():
                break

        print(
            "hook_counts:",
            dict(sorted(task.hook_counts.items())),
            "(after_compile includes construction/reset compilations)",
        )
    finally:
        env.close()


if __name__ == "__main__":
    main()
