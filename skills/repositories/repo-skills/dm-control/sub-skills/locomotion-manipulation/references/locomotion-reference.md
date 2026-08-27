# Locomotion, soccer, walkers, arenas, props, and mocap reference

`dm_control.locomotion` is a Composer-backed library for higher-level control tasks. It is organized around:

- **walkers**: movable agents such as CMU humanoids, rats/rodents, ants, and ball-with-head variants.
- **arenas**: floors, bowls, corridors, gaps/walls corridors, mazes, padded rooms, and textured maze components.
- **tasks**: rewards, observations, initialization, termination, and timing for locomotion objectives.
- **props and mocap data**: target spheres, motion-capture props, HDF5 trajectory loaders, and reference-pose tracking tasks.

Use the built-ins when the user wants a known locomotion/soccer/mocap task family. Route to `../composer-environments/SKILL.md` when the user wants to author new entity/task classes, custom observables, or new reward lifecycle logic.

## Built-in example constructors

These constructors return `composer.Environment` instances and can be inspected with `env.action_spec()`, `env.observation_spec()`, `env.reset()`, and a short step loop.

| Module | Constructors | Primary concepts | Caveats |
|---|---|---|---|
| `dm_control.locomotion.examples.basic_cmu_2019` | `cmu_humanoid_run_walls`, `cmu_humanoid_run_gaps`, `cmu_humanoid_go_to_target`, `cmu_humanoid_maze_forage`, `cmu_humanoid_heterogeneous_forage` | CMU humanoid walker; corridors, gaps, walls, floors, mazes, target spheres. | Maze variants use `labmaze` and texture assets from the installed package. |
| `dm_control.locomotion.examples.basic_rodent_2020` | `rodent_escape_bowl`, `rodent_run_gaps`, `rodent_maze_forage`, `rodent_two_touch` | Rat walker; bowl escape, gaps corridor, maze foraging, target touch timing. | Rodent tasks can be heavier than suite tasks; inspect briefly before long rollouts. |
| `dm_control.locomotion.examples.cmu_2020_tracking` | `cmu_humanoid_tracking` | CMU humanoid reference-pose/mocap tracking with CoMic-style reward. | May require CMU HDF5 mocap data and can trigger a large download if data is absent. |

Minimal example inspection pattern:

```python
from dm_control.locomotion.examples import basic_cmu_2019
import numpy as np

env = basic_cmu_2019.cmu_humanoid_go_to_target(random_state=np.random.RandomState(0))
print(env.action_spec())
print(env.observation_spec().keys())
time_step = env.reset()
```

Only run long training, viewer launchers, or mocap-tracking construction after confirming dependencies, assets, and runtime budget.

## Locomotion component map

Common public components you can import from the installed package:

- Arenas: `Floor`, `Bowl`, `EmptyCorridor`, `GapsCorridor`, `WallsCorridor`, `MazeWithTargets`, `RandomMazeWithTargets`, `PaddedRoom`, plus maze texture helpers.
- Walkers: `Ant`, `CMUHumanoidPositionControlled`, `CMUHumanoidPositionControlledV2020`, `JumpingBallWithHead`, `RollingBallWithHead`, `Rat`.
- Tasks: `RunThroughCorridor`, `Escape`, `GoToTarget`, `ManyGoalsMaze`, `ManyHeterogeneousGoalsMaze`, `RepeatSingleGoalMaze`, `RepeatSingleGoalMazeAugmentedWithTargets`, `TwoTouch`.
- Props: `TargetSphere`, `TargetSphereTwoTouch`, and mocap prop helpers.
- Mocap/reference-pose: `HDF5TrajectoryLoader`, trajectory wrappers, CMU mocap path helpers, `MultiClipMocapTracking`, and playback/reference-pose tasks.

The component classes are useful for choosing and lightly configuring built-ins. If a future task requires new lifecycle hooks, entity composition, observables, randomization distributions, or task classes, switch to the Composer sub-skill.

## Soccer environments

`dm_control.locomotion.soccer.load(...)` constructs multi-agent soccer environments:

```python
import numpy as np
from dm_control.locomotion import soccer

env = soccer.load(
    team_size=2,
    time_limit=10.0,
    disable_walker_contacts=False,
    enable_field_box=True,
    terminate_on_goal=False,
    walker_type=soccer.WalkerType.BOXHEAD,
    random_state=np.random.RandomState(0),
)

action_specs = env.action_spec()  # one spec per player
time_step = env.reset()
actions = [np.zeros(spec.shape, dtype=spec.dtype) for spec in action_specs]
time_step = env.step(actions)
```

Soccer choices:

- `team_size` must be between 1 and 11; total players are `team_size * 2`.
- `WalkerType.BOXHEAD` is the default and usually the lightest path.
- `WalkerType.ANT` uses ant walkers.
- `WalkerType.HUMANOID` uses humanoid walkers and mocap-based initialization; expect heavier assets and more setup.
- Rewards, discounts, and observations are per-player structures, not a single-agent scalar/dict.
- `terminate_on_goal=False` keeps play going after goals by resetting player/ball positions; `True` ends the episode on a goal.

## Asset, HDF5, and labmaze caveats

- Installed package assets should be used in place; do not copy meshes, textures, HDF5 data, or large model assets into downstream projects.
- `labmaze` is a normal package dependency used by maze arenas and examples. If maze imports fail, reinstall `dm_control` in a clean non-editable environment.
- HDF5 mocap loading requires `h5py`. If `HDF5TrajectoryLoader` reports missing `h5py`, install the public `h5py` package before running mocap/reference-pose tasks.
- CMU mocap helper functions may download hundreds of megabytes of HDF5 data when the expected cache is absent. Ask for budget/network permission before triggering them in automated workflows.
- Vision observations or viewer visualization require rendering support; route backend setup to `../rendering-viewer-assets/SKILL.md`.

## Inspect without long training

Use short, deterministic probes:

1. Import the module and constructor.
2. Construct only a lightweight environment first, such as `cmu_humanoid_go_to_target`, `rodent_escape_bowl`, or soccer `WalkerType.BOXHEAD` with small `team_size`.
3. Print `action_spec()` and `observation_spec()`.
4. Call `reset()` and at most one or a few `step()` calls with clipped zero/random actions.
5. Avoid interactive explorers and viewer launchers unless the user explicitly needs visualization and a rendering backend is verified.
6. Avoid mocap tracking constructors until `h5py`, data availability, download allowance, and runtime budget are clear.
